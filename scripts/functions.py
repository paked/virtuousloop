#!/usr/bin/env python3
# python ./scripts/functions.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''is a module that stores values for the scripts'''

import os
from time import strftime, localtime
import warnings
from functools import reduce
import subprocess
import unicodedata
import json
import yaml
from weasyprint import HTML as weasy
import readability
from bs4 import BeautifulSoup
import syntok.segmenter as segmenter
from aylienapiclient import textapi
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap
import pandas as pd
import config as c

# ===========================================================
# Organised into:
#   * warnings
#   * print colours
#   * load files
#   * print messages
#   * dataframe manipulations
#   * filesystem helpers
#   * console helpers
#   * print charts
# ===========================================================

# ===========================================================
#  warnings
# ===========================================================

warnings.filterwarnings("ignore", 'This pattern has match groups')

# ===========================================================
#  print colors
# ===========================================================


def pnt_info(text):
    print(bcolors.INFO + text + bcolors.ENDC)


def pnt_ok(text):
    print("\t" + bcolors.OK + text + bcolors.ENDC)


def pnt_warn(text):
    print("\t" + bcolors.WARNING + text + bcolors.ENDC)


def pnt_error(text):
    print(bcolors.ERROR + text + bcolors.ENDC)


def pnt_fail(text):
    print(bcolors.FAIL + text + bcolors.ENDC)


def pnt_notice(text, file):
    print(bcolors.NOTICE + text + file + bcolors.ENDC)

def pnt_console(text):
    print(text)

# ===========================================================
#  load files
# ===========================================================


def load_csv(file):
    try:
        test = open(c.f[file], encoding='utf-8', errors='ignore')
    except IOError:
        pnt_fail("Can't locate" + c.f[file] + c.msg['fail_warn'])
    else:
        pnt_ok ("Loaded " + c.f[file] + "...OK")
        # if the file has na as an index..
        if file == "crit_levels":
            c.df[file] = pd.read_csv(c.f[file], na_filter=False)
        elif file == "marks":
            c.df[file] = pd.read_csv(c.f[file], na_filter=False)
        else:
            c.df[file] = pd.read_csv(c.f[file])
        # lowercase all headers for simplification
        c.df[file].columns = map(str.lower, c.df[file].columns)


def load_tsv(file):
    try:
        test = open(c.t[file], encoding='utf-8', errors='ignore')
    except IOError:
        pnt_fail("Can't locate" + c.t[file] + "\n" + c.msg['fail_warn'])
    else:
        if "sorted" not in file: 
            pnt_ok ("Loaded " + c.t[file] + "...OK")
        # if the file has na as an index..
        if file == "crit_levels":
            c.df[file] = pd.read_csv(c.t[file], sep='\t', na_filter=False)
        elif file == "marks":
            c.df[file] = pd.read_csv(c.t[file], sep='\t', na_filter=False)
        else:
            c.df[file] = pd.read_csv(c.t[file], sep='\t')
        # lowercase all headers for simplification
        c.df[file].columns = map(str.lower, c.df[file].columns)
        return c.df[file]

def save_tsv(file):
    c.df[file].to_csv(c.t[file], sep='\t', encoding='utf-8', index=False)

def make_directories(folder):
    for key, value in folder.items():
        if not os.path.exists(value):
            os.makedirs(value)


def create_list(dataframe, column):
    this_list=[]
    for i, row in dataframe.iterrows():
        this_val = str(row[column])
        this_list.append(this_val)
    return this_list

def column_round(dataframe, column, dec_places):
    dataframe[column].round(decimals=dec_places)

# ===========================================================
#  print messages
# ===========================================================


def print_results_header(loop_row, out):
    '''print the header for all fields'''
    cfg = load_config()
    this_label = loop_row.label
    this_description = loop_row.description
    
    print("### " + this_label + "{-}\n\n", file=out)

    if cfg['crit_display']['label'] and not this_label:
        print(this_description + "\n\n", file=out)


def print_results_text(loop_row, record_row, out):
    '''option for displaying text results'''
    this_field = loop_row.field
    this_result = getattr(record_row, this_field)
    this_text_clean = BeautifulSoup(this_result, features="html5lib").get_text()
    print(this_text_clean + "\n\n", file=out)
    

def print_results_scale(loop_row, record_row, out):
    '''option for displaying scales'''
    this_field = loop_row.field
    this_result = getattr(record_row, this_field)
    this_image_url = "../../../files/scales/" + this_result + ".png"
    # if field == 'crit':
    print("![](" + this_image_url + ")\n\n", file=out)


def print_results_graph(loop_row, record_row, out):
    '''option for displaying graphs'''
    this_field = loop_row.field
    this_result = getattr(record_row, this_field)
    this_image = c.d['charts'] + this_field + "_" + this_result + ".png"
    print("Your performance in relation to others:\n\n", file=out)
    print("![](../../." + this_image + ")\n\n", file=out)

def print_new_page(out):
    print("\n\n<hr class=\"new_page\"></hr>\n\n", file=out)

def print_results_rubric(record_row, record):
    '''option for displaying rubric'''
    cfg = load_config()

    this_rubric = c.d['rubric'] + record + '.html'

    levels = filter_row('crit_levels', 'rubric', 'show')
    fields = filter_row('fields', 'field', 'crit_')

    # pandas record row
    print("record row")
    print(record_row)

    # string
    print("record")
    print(record)

    # crit description
    print("fields")
    print(fields)

    # N/HD etc
    print("levels")
    print(levels)

    with open(this_rubric, 'w') as out:

        with open(c.h['rubric_header'], "r") as header:
            print(header.read(), file=out)

        for level_row in levels.itertuples():
            this_col_header = level_row.text
            print("<th>" + this_col_header + "</th>", file=out)
        print("\n</tr>\n", file=out)

        # build table rows
        for field_row in fields.itertuples():
            # work through the crit fields
            this_field = field_row.field
            this_field_desc = this_field + "_desc"
            this_field_text = field_row.label
            this_field_weight = str(field_row.weight)

            # check the entry for this marks row
            this_marks_result = getattr(record_row, this_field)

            this_result_class_1 = ''
            this_result_class_2 = ''

            crit_levels = load_tsv('crit_levels')

            for level_row in crit_levels.itertuples():
                if this_marks_result == level_row.index:
                    this_result_class_1 = level_row.class1
                    this_result_class_2 = level_row.class2

            if (this_result_class_1 == this_result_class_2):
                flag = "flag100"
            else:
                flag = "flag50"

            # print the table headers
            print("<tr><th>" + this_field_text + "<br />" + this_field_weight + "%</th>", file=out)

            # work through the levels
            for level_row in levels.itertuples():
                # define the columns needed
                this_level_index = level_row.index
                this_level_text = getattr(level_row, this_field_desc)

                # start the cell
                print("<td", file=out)
                # add the flag if the level matches
                if (this_result_class_1 == this_level_index) or (this_result_class_2 == this_level_index):
                    print(" class=" + flag, file=out)

                # finish the cell
                print(">" + this_level_text + "</td>", file=out)
            print("</tr>", file=out)

        with open(c.h['rubric_footer'], "r") as footer:
            print(footer.read(), file=out)

        # add html header and style
        footer = open(c.h['rubric_footer'], "r")
        print(footer.read(), file=out)
        footer.close()


def print_comment_header(row, out):
    '''print the header for comments'''
    cfg = load_config()
    this_text = row.description
    print("### " + this_text + "{-}\n\n", file=out)


# ===========================================================
#  dataframe manipulations
# ===========================================================

def filter_row(dataframe, column, key):
    return c.df[dataframe][c.df[dataframe][column].str.contains(key)]

def filter_row_not(dataframe, column, key):
    return ~c.df[dataframe][c.df[dataframe][column].str.contains(key)]


def rename_header(dataframe, rename):
    '''used to standardise headers in a dataframe'''
    for key, val in rename.items():
        if key in c.df[dataframe].columns:
            pnt_warn("Replacing {} with {} ...now OK".format(key, val))

    c.df[dataframe].rename(columns=rename, inplace=True)


def rename_fields(dataframe, find, replace):
    pnt_warn("Replacing '" + find + "' with '" + replace + "' in " + dataframe + "...OK")
    # c.df[dataframe].replace(to_replace=find, value=replace, inplace=False)
    c.df[dataframe].replace(to_replace=find, value=replace, regex=True, inplace=True)


def check_for_empty_cells(dataframe, required_columns):
    for column in required_columns:
        try:
            if c.df[dataframe][column].isnull().values.any():
                pnt_error("WARNING: There are empty cells in " + dataframe + "/" + column + ". Please fix the csv or the script may not behave as expected.")
                if dataframe != 'students':
                    this_dataframe=c.df[dataframe][required_columns]
                    print(this_dataframe[this_dataframe[column].isnull()])
        except Exception:
            pnt_fail("ERROR: The column '" + column + "'' does not exist in " + dataframe + ".csv. Please fix the csv or the script may fail.")


def check_for_duplicates(dataframe, column):
    if any(c.df[dataframe].duplicated()):
        print(dataframe)
        pnt_fail(c.msg['check_dupes'] + dataframe + ':')
        # print duplicate rows to the console
        print(c.df[dataframe][c.df[dataframe].duplicated(subset=[column], keep='last')][[column]])
        # only use the final duplicate
        c.df[dataframe].drop_duplicates(subset=[column], keep='last', inplace=True)


def col_to_lower(dataframe, column):
    if column in c.df[dataframe].columns:
        c.df[dataframe][column] = c.df[dataframe][column].str.lower()


def check_for_columns(this_csv):
    load_csv('fields')
    col_to_lower('fields', 'field')
    crit_df = filter_row('fields', 'field', 'crit_')
    crit_list = create_list(crit_df, 'field')
    this_csv = c.df[this_csv]

    for crit in crit_list:
        if crit not in this_csv.columns:
            this_csv[crit] = '0'


def check_for_labels(this_csv):
    load_csv('fields')
    col_to_lower('fields', 'field')
    crit_df = filter_row('fields', 'field', 'crit_')
    crit_list = create_list(crit_df, 'label')
    # load_csv('this_csv')
    # print(c.df[this_csv])
    this_list_a = create_list(c.df[this_csv], 'crita_text')
    this_list_b = create_list(c.df[this_csv], 'critb_text')
    this_list = this_list_a + this_list_b
    this_list = set(this_list)
    difference = diff_between_lists(crit_list, this_list)

    if difference:
        for item in difference:
            pnt_fail("FATAL ERROR: please fix " + this_csv + ".csv or fields.csv")
            pnt_fail("\tThe value \"" + item + "\" exists in " + this_csv + " but not in fields.csv")
        exit()



def diff_between_lists(list1, list2):
    union = set(list1).union(set(list2))
    intersection = set(list1).intersection(set(list2))
    return list(union - intersection)
    
    this_csv = c.df[this_csv]

    for crit in crit_list:
        if crit not in this_csv.columns:
            this_csv[crit] = '0'


def many_eyes_dataframe_sort(dataframe):
    cfg = load_config()
    this_df = c.df[dataframe].copy()
    this_a_df = this_df[['username', 'user', 'team', 'crit_a', 'crita_text', 'crita_comment']].copy()
    this_b_df = this_df[['username', 'user', 'team', 'crit_b', 'critb_text', 'critb_comment']].copy()
    this_a_df.rename(columns={'crit_a': 'crit_val'}, inplace=True)
    this_a_df.rename(columns={'crita_text': 'crit_text'}, inplace=True)
    this_a_df.rename(columns={'crita_comment': 'crit_comment_html'}, inplace=True)
    this_b_df.rename(columns={'crit_b': 'crit_val'}, inplace=True)
    this_b_df.rename(columns={'critb_text': 'crit_text'}, inplace=True)
    this_b_df.rename(columns={'critb_comment': 'crit_comment_html'}, inplace=True)
    this_frames = [this_a_df, this_b_df]
    this_dataframe = pd.concat(this_frames, ignore_index=True, sort=False)
    this_dataframe['crit_desc'] = this_dataframe['crit_val']
    this_dataframe['crit_val'].replace(cfg['audit_chart']['find_labels'], cfg['audit_chart']['replace_values'], inplace=True) 
    this_dataframe['crit_comment_txt'] = this_dataframe['crit_comment_html'].mask(pd.isnull, "No Comment")
    this_dataframe['crit_comment_clean'] = [BeautifulSoup(text, features="html5lib").get_text() for text in this_dataframe['crit_comment_txt'] ]

    for i, row in this_dataframe.iterrows():
        this_html = BeautifulSoup(row['crit_comment_clean'], 'html.parser')
        replace = ('\r', ' '), ('\n', ' '), ('  ', ' '), ("\"", "\'")
        this_text = reduce(lambda a, kv: a.replace(*kv), replace, this_html.get_text())
        text_clean = unicodedata.normalize("NFKD", this_text)
        this_dataframe.at[i,'crit_comment'] = text_clean

    this_dataframe[['username', 'user', 'team', 'crit_val', 'crit_desc', 'crit_text', 'crit_comment']].to_csv(c.t[dataframe + "_sorted"], sep='\t', encoding='utf-8', index=False)

# ===========================================================
#  readability helpers
# ===========================================================


def readability_stats(dataframe, row, i, current_column, new_column, readability_group, readability_measure):
    this_comment = row[current_column]
    tokenized = '\n\n'.join(
        '\n'.join(' '.join(token.value for token in sentence)
                for sentence in paragraph)
    for paragraph in segmenter.analyze(this_comment))
    this_result = readability.getmeasures(tokenized, lang='en')
    c.df[dataframe].at[i,new_column] = this_result[readability_group][readability_measure]


def html_to_text(text_raw):
    this_html = BeautifulSoup(text_raw, 'html.parser')
    replace = ('\r', ' '), ('\n', ' '), ('  ', ' '), ("\"", "\'")
    this_text = reduce(lambda a, kv: a.replace(*kv), replace, this_html.get_text())
    text_clean = unicodedata.normalize("NFKD", this_text)
    return text_clean

# ===========================================================
#  pandoc helpers
# ===========================================================


def pandoc_yaml(out, record): 
    cfg = load_config()
    print("---", file=out)
    print("title: " + record, file=out)
    print("date: Generated " + strftime("%Y-%m-%d %H:%M:%S", localtime()), file=out)
    for i in cfg['assignment']:
        print(i + ": " + cfg['assignment'][i], file=out)
    for i in cfg["pdf_front_matter"]:
        print(i + ": " + cfg["pdf_front_matter"][i], file=out)
    print("---\n\n", file=out)


def pandoc_css(out, record, kind): 
    cfg = load_config()
    now = strftime("%Y-%m-%d %H:%M:%S", localtime())
    print("@page {", file=out)
    if (kind == 'conf'):
        print("background-image: url(../../../includes/pdf/watermark_confidential.png);", file=out)
    print("@top-left {", file=out)
    print("content: '" + cfg["assignment"]["assignment_title"] + "';}", file=out)
    print("@bottom-left {", file=out)
    print("content: '" + cfg["pdf_front_matter"]["copyright"] + "';}", file=out)
    print("@bottom-right {", file=out)
    print("content: 'Generated " + now + "';}", file=out)
    print("}", file=out)
    print("html body article#cover {", file=out)
    if (kind == 'conf'):
        print("background-color: #D38C98;}", file=out)
    else:
        print("background-color: #C7DDE8;}", file=out)
    print("@page :first {", file=out)
    if (kind == 'conf'):
        print("background-image: url(../../../includes/pdf/watermark_confidential.png);}", file=out)


def pandoc_html_toc(this_file, this_record, kind):
    subprocess.call("pandoc -s -t html5 \
        --toc -c ../../../includes/pdf/report.css \
        -c ../../." + c.d["css"] + this_record + "_" + kind + ".css \
        --metadata-file=" + c.d["yaml"] + this_record + ".yaml \
        --template=./includes/pdf/pandoc_report.html \
        " + c.d["md"] + this_file + ".md \
        -o " + c.d["html"] + this_file + ".html", shell=True)


def pandoc_html(this_file, this_record, kind):
    subprocess.call("pandoc -s -t html5 \
        -c ../../../includes/pdf/single.css \
        -c ../../." + c.d["css"] + this_record + "_" + kind + ".css \
        --metadata-file=" + c.d["yaml"] + this_record + ".yaml \
        --template=./includes/pdf/pandoc_single.html \
        " + c.d["md"] + this_file + ".md \
        -o " + c.d["html"] + this_file + ".html", shell=True)


def pandoc_html_single(this_file):
    cfg = load_config()
    try:
        subprocess.call("pandoc -s -t html5 \
                            -c ../../../includes/pdf/single.css \
                            -c ../../." + c.d["css"] + this_file + ".css \
                            --metadata-file=" + c.d["yaml"] + this_file + ".yaml \
                            --template=./includes/pdf/pandoc_single.html \
                            " + c.d["md"] + this_file + ".md \
                            -o " + c.d["html"] + this_file + ".html", shell=True)
    except Exception:
        f.pnt_fail("Unable to create " + this_file + "feedback file")


def pandoc_pdf(this_file):
    '''Old function, outdates name, replaced by weasy_pdf'''
    try:
        weasy(c.d["html"] + this_file + ".html").write_pdf(c.d["pdf"] + this_file + ".pdf")
    except Exception:
        print(this_file + " cannot be converted")

def weasy_pdf(this_file):
    try:
        weasy(c.d["html"] + this_file + ".html").write_pdf(c.d["pdf"] + this_file + ".pdf")
    except Exception:
        print(this_file + " cannot be converted")

# ===========================================================
#  filesystem helpers
# ===========================================================


def load_config():

    # Read default YAML file
    with open("./includes/config_defaults.yml", 'r') as stream:
        config_defaults = yaml.safe_load(stream)

    # Read local configuration
    with open("./files/app_config.yml", 'r') as stream:
        app_config = yaml.safe_load(stream)

    # Replace defaults with local config
    config_defaults.update(app_config)
    return config_defaults


def file_exists(file):
    try:
        this_file = open(file)
    except IOError:
        f.pnt_fail(c.msg['console_app_config_fail'])
    else:
        return yaml.safe_load(this_file)

# ===========================================================
#  console helpers
# ===========================================================


# ===========================================================
#  print chart 
# ===========================================================


def make_crit_list(crit, dataframe):
    crit_levels = load_tsv('crit_levels')
    crit_list = [crit_levels]
    for i, crit_row in crit.iterrows():
        this_crit = crit_row['field']
        this_crit = dataframe[this_crit].value_counts().reset_index()
        crit_list.append(this_crit)
    crit_list = [df.set_index('index') for df in crit_list]
    return (crit_list[0].join(crit_list[1:]))


def make_crit_chart(crit, stats, name):
    cfg = load_config()
    for i, crit_row in crit.iterrows():
        this_crit = crit_row["field"]
        for pos in range(len(stats)):
            this_value = stats.text[pos]
            ax = stats[[this_crit]].plot(kind="bar", title ="", figsize=(10, 3), width=1.0, legend=False, fontsize=8, color="#23537D")
            ax.patches[pos].set_facecolor("#26AD63")
            ax.set_xlabel("", fontsize=8)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
            ax.get_yaxis().set_ticks([])
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.spines["top"].set_visible(False)
            if name == "na":
                out = c.d["charts"] + this_crit + "_" + this_value + ".png"
            else:
                out = c.d["charts"] + this_crit + "_" + name + "_" + this_value + ".png"
            plt.savefig(out, bbox_inches="tight")
            plt.clf()

def make_count_chart(dataframe, name):
    cfg = load_config()
    ax = dataframe.plot(kind='bar', title ="", figsize=(10, 3), width=1.0, legend=True, fontsize=8, colormap=cfg['tmc_chart']['colormap'])
    ax.set_xlabel("", fontsize=8)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.get_yaxis().set_ticks([])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    leg = plt.legend( loc = 'lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.4
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform = ax.transAxes)
    if name == "na":
        out = c.d['charts'] + "count_" + ".png"
    else:
        out = c.d['charts'] + "count_" + name + ".png"
    plt.savefig(out, bbox_inches='tight')
    plt.clf()

def make_stacked_chart(dataframe, name, boolean):
    cfg = load_config()
    dataframe.fillna(0, inplace=True)
    if boolean:
        dataframe['average'] = dataframe.mean(axis=1)
    dataframe = dataframe.set_index('index')
    this_dataframe = dataframe.T
    print(this_dataframe)
    ax = this_dataframe.plot(kind='barh', stacked=True, title ="", figsize=(10, 3), width=1.0, legend=True, fontsize=8, colormap=cfg['tmc_chart']['colormap'])
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    leg = plt.legend( loc = 'lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.4
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform = ax.transAxes)
    if name == "na":
        out = c.d['charts'] + "count_" + ".png"
    else:
        out = c.d['charts'] + "count_" + name + ".png"
    plt.savefig(out, bbox_inches='tight')
    plt.clf()


def make_col_chart(dataframe, col, role, chart_min, chart_max):
    cfg = load_config()
    if role == 'self':
        this_color = "#23537D"
    else:
        this_color = "#26AD63"
    ax = dataframe.hist(column=col, color=this_color, bins=20, grid=False, figsize=(10,3), zorder=2, rwidth=0.9, range=(chart_min, chart_max))
    ax = ax[0]
    for x in ax:
        x.spines['right'].set_visible(False)
        x.spines['top'].set_visible(False)
        x.spines['left'].set_visible(False)
        x.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")
        vals = x.get_yticks()
        for tick in vals:
            x.axhline(y=tick, linestyle='dashed', alpha=0.4, color='#eeeeee', zorder=1)
        x.set_title("")
        x.set_xlabel("", labelpad=20, weight='bold', size=12)
        x.set_ylabel("Frequency", labelpad=20, weight='bold', size=12)
        # x.yaxis.set_major_formatter(StrMethodFormatter('{x:,g}'))
    out = c.d['charts'] + col + "_" + role + ".png"
    plt.savefig(out, bbox_inches='tight')
    plt.clf()

def make_hist_chart(dataframe, col):
    this_color = "#23537D"
    ax = dataframe.hist(column=col, color=this_color, bins=20, grid=False, figsize=(10,4), zorder=2, rwidth=0.9, range=(0, 100))
    ax = ax[0]
    for x in ax:
        x.spines['right'].set_visible(False)
        x.spines['top'].set_visible(False)
        x.spines['left'].set_visible(False)
        x.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")
        vals = x.get_yticks()
        for tick in vals:
            x.axhline(y=tick, linestyle='dashed', alpha=0.4, color='#eeeeee', zorder=1)
        x.set_title("")
        x.set_xlabel("", labelpad=20, weight='bold', size=12)
        x.set_ylabel("Frequency", labelpad=20, weight='bold', size=12)
        # x.yaxis.set_major_formatter(StrMethodFormatter('{x:,g}'))
    out = c.d['charts'] + col + ".png"
    plt.savefig(out, bbox_inches='tight')
    plt.clf()

def make_boxplot_chart(dataframe, col):
    ax = dataframe.boxplot(column=col, by='marker', grid=False, figsize=(10,4), zorder=2, vert=False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")
    vals = ax.get_yticks()
    for tick in vals:
        ax.axhline(y=tick, linestyle='dashed', alpha=0.4, color='#eeeeee', zorder=1)
    ax.set_title("")
    ax.set_xlabel("", labelpad=20, weight='bold', size=12)
    ax.set_ylabel("", labelpad=20, weight='bold', size=12)
    out = c.d['charts'] + col + "_boxplot.png"
    plt.savefig(out, bbox_inches='tight')
    plt.clf()

def make_stat_chart(dataframe, group_axis, count_axis, title):
    cfg = load_config()
    this = dataframe.groupby(group_axis)[count_axis].mean()
    # this.columns = [x.strip().replace('_', ' ') for x in this.columns]
    # this.head()
    this_colormap = cm.get_cmap(cfg['tmc_chart']['colormap'], 512)
    limited_colormap = ListedColormap(this_colormap(np.linspace(0.25, 0.75, 256)))
    this_title = cfg['crit_chart'][title]
    ax = this.plot(kind='barh', title ="", figsize=(10, 3), width=1.0, legend=True, fontsize=8, colormap=limited_colormap)
    ax.tick_params(axis="both", which="both", bottom="off", top="off", labelbottom="on", left="off", right="off", labelleft="on")
    ax.set_xlabel(this_title.replace("_", " ").capitalize(), labelpad=20, size=8, weight='bold')
    ax.set_ylabel(group_axis.replace("_", " ").capitalize(), labelpad=20, size=8, weight='bold')
    leg = plt.legend( loc = 'lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.5
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform = ax.transAxes)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    out = c.d['charts'] + title + ".png"
    plt.tight_layout()
    plt.savefig(out, bbox_inches='tight')
    plt.clf()


def make_tmc_chart(dataframe, out):
    cfg = load_config()
    ax = dataframe.plot(kind='bar', title ="", figsize=(10, 3), legend=True, fontsize=10, colormap=cfg['tmc_chart']['colormap'], width=0.5)
    ax.set_xlabel(cfg['tmc_chart']['x_axis_title'], fontsize=10)
    ax.set_xticklabels(ax.get_xticklabels(),rotation=0)
    ax.set_yticks(cfg['tmc_chart']['y_tick_values']) 
    ax.set_yticklabels(cfg['tmc_chart']['y_tick_labels'])
    ax.set_ylabel(cfg['tmc_chart']['y_axis_title'], fontsize=10)
    ax.axhline(0, color='black', lw=1)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    leg = plt.legend( loc = 'lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.5
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform = ax.transAxes)
    plt.ylim(-2, 2)
    plt.tight_layout()
    plt.savefig(out, bbox_inches='tight')
    plt.clf()


def make_audit_chart(dataframe, out):
    cfg = load_config()
    ax = dataframe.plot(kind='bar', title ="", figsize=(10, 3), legend=True, fontsize=10, colormap=cfg['audit_chart']['colormap'], width=0.5)
    ax.set_xlabel(cfg['audit_chart']['x_axis_title'], fontsize=10)
    ax.set_xticklabels(ax.get_xticklabels(),rotation=0)
    ax.set_yticks(cfg['audit_chart']['y_tick_values']) 
    ax.set_yticklabels(cfg['audit_chart']['y_tick_labels'])
    ax.set_ylabel(cfg['audit_chart']['y_axis_title'], fontsize=10)
    ax.axhline(0, color='black', lw=1)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    leg = plt.legend(loc='lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.5
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)        
    plt.ylim(-2, 4)
    plt.tight_layout()
    plt.savefig(out, bbox_inches='tight')
    plt.clf()


def make_audit_crit_chart(dataframe, out):
    cfg = load_config()
    ax = dataframe.plot(kind='bar', title ="", figsize=(10, 3), legend=True, fontsize=10, colormap=cfg['audit_chart']['colormap'], width=0.5)
    ax.set_xlabel(cfg['audit_chart']['x_axis_title'], fontsize=10)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.set_yticks(cfg['audit_chart']['y_tick_values']) 
    ax.set_yticklabels(cfg['audit_chart']['y_tick_labels'])
    ax.set_ylabel(cfg['audit_chart']['y_axis_title'], fontsize=10)
    ax.axhline(0, color='black', lw=1)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    leg = plt.legend(loc='lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.5
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)        
    plt.ylim(-2, 4)
    plt.tight_layout()
    plt.savefig(out, bbox_inches='tight')
    plt.clf()


def make_feedback_chart(dataframe, out):
    cfg = load_config()
    ax = dataframe.plot(kind='bar', title ="", figsize=(10, 3), legend=True, fontsize=10, colormap=cfg['audit_chart']['colormap'], width=0.5)
    ax.set_xlabel("", fontsize=8)
    x_tick_labels = dataframe.index.values
    ax.set_xticklabels(x_tick_labels, rotation=0)
    ax.set_ylabel('Percentage', labelpad=20, size=8, weight='bold')    
    ax.axhline(0, color='black', lw=1)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    leg = plt.legend(loc='lower center', ncol=8)
    bb = leg.get_bbox_to_anchor().inverse_transformed(ax.transAxes)
    yOffset = 0.5
    bb.y0 -= yOffset
    bb.y1 -= yOffset
    leg.set_bbox_to_anchor(bb, transform=ax.transAxes)        
    # plt.ylim(0, 50)
    plt.tight_layout()
    plt.savefig(out, bbox_inches='tight')
    plt.clf()


class bcolors:
    INFO = '\033[95m'
    NOTICE = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[36m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def text_analysis_api(text, label, record):
    '''
    function to call nlp api
    '''
    cfg = load_config()
    aylien = textapi.Client(cfg['aylien']['api_id'], cfg['aylien']['api_key'])
    combined = aylien.Combined({
        'text': text,
        'endpoint': cfg['aylien']['endpoints']
    })

    this_dict = dict()
    for result in combined["results"]:
        this_endpoint = result["endpoint"]
        this_result = result["result"]
        if this_endpoint == "entities":
            try:
                this_dict['entities'] = this_result["entities"]["keyword"]
            except Exception:
                this_dict['entities'] = ["None detected"]
        if this_endpoint == "sentiment":
            try:
                this_dict['polarity'] = this_result["polarity"]
            except Exception:
                this_dict['polarity'] = ["None detected"]
        if this_endpoint == "hashtags":
            try:
                this_dict['hashtags'] = this_result["hashtags"]
            except Exception:
                this_dict['polarity'] = ["None detected"]
        if this_endpoint == "summarize":
            try:
                this_dict['sentences'] = this_result["sentences"]
            except Exception:
                this_dict['sentences'] = ["None detected"]
    this_dict_dump = json.dumps(this_dict)
    return this_dict_dump


def sentiment_table(columns, rows):
    cfg = load_config()
    sentiment_columns = ["Name"]
    sentiment_list = []
    # set up the columns
    for i, row in columns.iterrows():
        field_text = row['label']
        sentiment_columns.append(field_text)

    # work through the rows
    for num, endpoint in enumerate(cfg['aylien']['endpoints'], start=0):
        name = (cfg['aylien']['endpoint_name'][num])
        if endpoint == 'sentiment':
            for i, row in rows.iterrows():
                this_marker_name = row['marker_name']
                sentiment_rows = [this_marker_name]
                for i, row in columns.iterrows():
                    comment = row['field']
                    with open(c.d['nlp'] + this_marker_name + "_" + comment + ".json") as json_file:
                        this_nlp = json.load(json_file)
                        try:
                            item_out = ""
                            for item in this_nlp[name]:
                                item_out += item
                            sentiment_rows.append(item_out)
                        except Exception:
                            sentiment_rows.append("N/A")
                sentiment_list.append(sentiment_rows)
    # return the result
    return pd.DataFrame(sentiment_list, columns=sentiment_columns)

def print_credit():
    with open("./includes/pdf/ascii.txt", "r") as credit:
            print(credit.read())
