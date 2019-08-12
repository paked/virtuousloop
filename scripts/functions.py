#!/usr/bin/env python3
# python ./scripts/functions.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''is a module that stores values for the scripts'''

import os
import pandas as pd
import config as c
from time import gmtime, strftime, localtime
import yaml
import warnings
import sys
import time
import matplotlib.pyplot as plt
from weasyprint import HTML as weasy
from unidecode import unidecode
import readability
from bs4 import BeautifulSoup
from functools import reduce
import syntok.segmenter as segmenter
from aylienapiclient import textapi
from jq import jq


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

def pnt_fail(text):
    print(bcolors.FAIL + text + bcolors.ENDC)

def pnt_notice(text,file):
    print(bcolors.NOTICE + text + file + bcolors.ENDC)

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
        pnt_fail("Can't locate" + c.t[file] + c.msg['fail_warn'])
    else:
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

def make_directories(folder):
    for key, value in folder.items():
        if not os.path.exists(value):
            os.makedirs(value)

def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])

def correctSubtitleEncoding(filename, newFilename, encoding_from, encoding_to='UTF-8'):
    with open(filename, 'r', encoding=encoding_from) as fr:
        with open(newFilename, 'w', encoding=encoding_to) as fw:
            for line in fr:
                fw.write(line[:-1]+'\r\n')

    # print(tsv.groupby(['group']).size())

# ===========================================================
#  print messages
# ===========================================================

def print_results_header(field, row, m_row, out):
    ## print the header for all fields
    cfg = config_exists()
    this_field = str(row['field'])
    this_text = str(row['text'])
    this_label = str(row['label'])

    print("### " + this_text + "{-}\n\n", file=out)
    if (cfg['crit_display']['label'] == 'true'):
        print(this_label + "\n\n", file=out)

def print_results_text(field, row, m_row, out):
    # option for displaying text results
    this_field = row['field']
    this_result = m_row[this_field]
    this_result_text = filter_row('crit_levels', 'index', '^' + this_result + '$').text.to_string(index=False).lstrip()

    if field == 'crit':
        print("**" + this_result_text + "**\n\n", file=out)
    else: 
        print(this_result + "\n\n", file=out)

def print_results_scale(field, row, m_row, out):
    # option for displaying scales
    this_field = row['field']
    this_result = m_row[this_field]
    this_image = filter_row('crit_levels', 'index', '^' + this_result + '$').img.to_string(index=False).lstrip()
    if field == 'crit':
        print("![](" + c.d['scales'] + this_image + ")\n\n", file=out)

def print_results_graph(field, row, m_row, out):
    # option for displaying graphs
    this_field = row['field']
    this_image = c.d['graphs'] + this_field + ".pdf"
    if field == 'crit':
        print("![](" + this_image + ")\n\n", file=out)

def print_results_rubric(out, m_row, record):
    # option for displaying rubric
    cfg = config_exists()

    this_rubric = c.d['rubric'] + record + '.html'
    this_rubric_pdf = c.d['rubric'] + record + '.pdf'
    levels=filter_row('crit_levels', 'rubric', 'show')
    fields=filter_row('fields', 'field', 'crit_')
    with open(this_rubric, 'w') as rubric_out:

        # add html header and style
        header = open(c.h['wkhtml_header'], "r")
        print(header.read(), file=rubric_out)
        header.close()

        # add table header
        print("<table>\n<tr><th>Criteria</th>\n", file=rubric_out)
        for i, l_row in levels.iterrows():
            this_col_header = l_row['text']
            print("<th>" + this_col_header + "</th>", file=rubric_out)
        print("\n</tr>\n", file=rubric_out)

        # build table rows
        for j, f_row in fields.iterrows():
            # work through the crit fields
            this_row = f_row['field']
            this_row_desc = this_row + "_desc"
            this_row_text = f_row['text']
            this_row_weight = str(f_row['weight'])

            # check the entry for this marks row
            this_marks_result = m_row[this_row]
            this_result_class_1 = filter_row('crit_levels', 'index', '^' + this_marks_result + '$').class1.to_string(index=False).lstrip()
            this_result_class_2 = filter_row('crit_levels', 'index', '^' + this_marks_result + '$').class2.to_string(index=False).lstrip()
            # choose the flag
            if (this_result_class_1 == this_result_class_2) :
                flag = "flag100"
            else:
                flag = "flag50"

            # print the table headers
            print("<tr><th>" + this_row_text + "<br />" + this_row_weight + "%</th>", file=rubric_out)
            
            # work through the levels
            for i, l_row in levels.iterrows():
                # define the columns needed
                this_level_index = l_row['index']
                this_level_text = l_row[this_row_desc]
                this_level_class_1 = l_row['class1']
                this_level_class_2 = l_row['class2']

                # start the cell
                print("<td", file=rubric_out)

                # add the flag if the level matches
                if (this_result_class_1 == this_level_index) or (this_result_class_2 == this_level_index):
                    print(" class=" + flag, file=rubric_out)

                # finish the table
                print(">" + this_level_text + "</td>", file=rubric_out)
            print("</tr>", file=rubric_out)
        print("</table>", file=rubric_out)

        # add html header and style
        footer = open(c.h['wkhtml_footer'], "r")
        print(footer.read(), file=rubric_out)
        footer.close()

    weasy(this_rubric).write_pdf(this_rubric_pdf)

    print("![](" + this_rubric_pdf + ")", file=out)

# ===========================================================
#  dataframe manipulations
# ===========================================================

def filter_row(dataframe, column, key):
    return c.df[dataframe][c.df[dataframe][column].str.contains(key)]


def rename_header(dataframe, find, replace):
    if find in c.df[dataframe].columns:
        pnt_warn("Replacing '" + find + "' with '" + replace + "'...OK")
        c.df[dataframe].rename(columns={find: replace}, inplace=True)
    #else:
    #   pnt_fail("\tCould not find '" + find + "' as headers in " + dataframe + "'...not replaced")

def rename_fields(dataframe, find, replace):
    pnt_warn("Replacing '" + find + "' with '" + replace + "' in " + dataframe + "...OK")
    # c.df[dataframe].replace(to_replace=find, value=replace, inplace=False)
    c.df[dataframe].replace(to_replace= find, value= replace, regex=True, inplace=True)


def check_duplicates(dataframe, column):
    if any(c.df[dataframe].duplicated()) is True:
        pnt_fail(c.msg['check_dupes'] + dataframe + ':')
        # print duplicate rows to the console
        print(c.df[dataframe][c.df[dataframe].duplicated(subset=[column], keep='last')][['user']])
        # only use the final duplicate
        c.df[dataframe].drop_duplicates(subset=[column], keep='last', inplace=True)

def col_to_lower(dataframe, column):
    if column in c.df[dataframe].columns:
        c.df[dataframe][column] = c.df[dataframe][column].str.lower()

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

def html_to_text(dataframe, row, i, current_column, new_column):
    this_html = BeautifulSoup(row[current_column], 'html.parser')
    replace = ('\r', ' '), ('\n', ' '), ('  ', ' ')
    this_text = reduce(lambda a, kv: a.replace(*kv), replace, this_html.get_text())
    c.df[dataframe].at[i,new_column] = this_text


# ===========================================================
#  pandoc helpers
# ===========================================================

def pandoc_header(out, record): 
    cfg = config_exists()

    print("---", file=out)
    print("title: " + record, file=out)
    print("date: Generated " + strftime("%Y-%m-%d %H:%M:%S", localtime()), file=out)
    for i in cfg['assignment']:
        print(i + ": " + cfg['assignment'][i], file=out)
    for i in cfg["pdf_front_matter"]:
        print(i + ": " + cfg["pdf_front_matter"][i], file=out)
    print("---\n\n", file=out)
    print("# " + cfg['assignment']['assignment_title'] + " Feedback{-}\n\n", file=out)
    print("# " + record + "{-}\n\n\n", file=out)

def pandoc_pdf(this_file):
    subprocess.call("pandoc " + this_file + ".md -o " + this_file + ".pdf --template=./includes/pdf/anu_cecs.latex --pdf-engine=xelatex", shell=True)

# ===========================================================
#  filesystem helpers
# ===========================================================

def config_exists():
    #pnt_notice(c.msg['console_app_config_check'],os.path.basename(__file__))
    try:
        config = open('./files/app_config.yml')
    except IOError:
        f.pnt_fail(c.msg['console_app_config_fail'])
    else:
        return yaml.safe_load(config)

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

def progress_bar (iteration, upper, suffix, prefix = '', decimals = 1, length = 50, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        upper       - Required  : upper iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(upper)))
    filledLength = int(length * iteration // upper)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # print new line on complete
    if iteration == upper: 
        print()

# ===========================================================
#  print chart 
# ===========================================================

def make_crit_list(crit):
    crit_levels=load_tsv('crit_levels')
    marks=load_tsv('marks')

    crit_list=[crit_levels]
    for i, crit_row in crit.iterrows():
        this_crit = crit_row['field']
        this_crit=marks[this_crit].value_counts().reset_index()
        crit_list.append(this_crit)
    crit_list = [df.set_index('index') for df in crit_list]
    return (crit_list[0].join(crit_list[1:]))

def make_crit_chart(crit, stats):
    for i, crit_row in crit.iterrows():
        this_crit = crit_row['field']
        ax = stats[[this_crit]].plot(kind='bar', title ="", figsize=(10, 2), width=0.9, legend=False, fontsize=8)
        ax.set_xlabel("", fontsize=8)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        ax.set_yticklabels("", rotation=0)
        ax.get_yaxis().set_ticks([])
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['top'].set_visible(False)
        out = c.d['graphs'] + this_crit + ".pdf"
        plt.savefig(out, bbox_inches='tight')

def make_tmc_chart(dataframe, out):
    cfg = config_exists()
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

class bcolors:
    INFO = '\033[95m'
    NOTICE = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# function to call api
def text_analysis_api (text, label, record):
    cfg=config_exists()
    print(record)
    this_nlp = c.d['nlp'] + record + '-' + label + '.json'
    aylien = textapi.Client(cfg['aylien']['api_id'], cfg['aylien']['api_key'])
    combined = aylien.Combined({
        'text': text,
        #'endpoint': ["sentiment", "classify", "extract", "summarize", "entities", "hashtags", "concepts"]
        'endpoint': ["entities", "summarize"]
    })

    with open(this_nlp, 'w') as out:
        print(combined["results"], file=out)


    for result in combined["results"]:
        print(result["endpoint"])
        print(result["result"])
        print(jq(".keyword[]").transform(result["result"]))


    # # extract keywords
    # for type in self shadow; do
    #     jq '.results[1].result.entities.keyword[]' ./reviews/api/"$this_user"-"$type".txt | sed 's/ .*//g;s/"//g;s/\(.*\)/\L\1/;' | sort -u | sed '$!N; /\(.*\)\n\1s/!P;D;' > ./reviews/keywords/"$this_user"-"$type".txt
    # done

    # # extract hashtags
    # for type in self shadow; do
    #     jq '.results[4].result.hashtags[]' ./reviews/api/"$this_user"-"$type".txt | sed 's/ .*//g;s/"//g;s/\(.*\)/\L\1/;' | sort -u | sed '$!N; /\(.*\)\n\1s/!P;D;' > ./reviews/hashtags/"$this_user"-"$type".txt
    # done

#     this_nlp = c.d['reviews'] + user + '-' + label + '.txt'
#     with open(this_nlp, 'w') as out:
#         this_result=curl -s 'https://api.aylien.com/api/v1/combined' \
#            -H "X-AYLIEN-TextAPI-Application-Key: " + cfg['aylien']['api_key'] \
#            -H "X-AYLIEN-TextAPI-Application-ID: " + cfg['aylien']['api_id']  \
#            --data-urlencode "text=$this_text_self" \
#            --data-urlencode "endpoint=sentiment" \
#            --data-urlencode "endpoint=classify" \
#            --data-urlencode "endpoint=extract" \
#            --data-urlencode "endpoint=summarize" \
#            --data-urlencode "endpoint=entities" \
#            --data-urlencode "endpoint=hashtags" \
#            --data-urlencode "endpoint=concepts"
#         print(this_result, file=out)