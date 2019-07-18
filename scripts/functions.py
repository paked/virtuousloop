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


warnings.filterwarnings("ignore", 'This pattern has match groups')

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

def load_csv(file):
    try:
        test = open(c.f[file])
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
        test = open(c.t[file])
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

def print_results_header(field, row, m_row, out):
    ## print the header for all fields
    conf = config_exists()
    this_field = str(row['field'])
    this_text = str(row['text'])
    this_label = str(row['label'])

    print("### " + this_text + "{-}\n\n", file=out)
    if (conf['crit_display']['label'] == 'true'):
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
    conf = config_exists()

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

def pandoc_header(out, record): 
    conf = config_exists()

    print("---", file=out)
    print("title: " + record, file=out)
    print("date: Generated " + strftime("%Y-%m-%d %H:%M:%S", localtime()), file=out)
    for i in conf['assignment']:
        print(i + ": " + conf['assignment'][i], file=out)
    for i in conf["pdf_front_matter"]:
        print(i + ": " + conf["pdf_front_matter"][i], file=out)
    print("---\n\n", file=out)
    print("# " + conf['assignment']['assignment_title'] + " Feedback{-}\n\n", file=out)
    print("# " + record + "{-}\n\n", file=out)


def config_exists():
    #pnt_notice(c.msg['console_app_config_check'],os.path.basename(__file__))
    try:
        config = open('./files/app_config.yml')
    except IOError:
        f.pnt_fail(c.msg['console_app_config_fail'])
    else:
        return yaml.safe_load(config)

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
    conf = config_exists()
    ax = dataframe.plot(kind='bar', title ="", figsize=(10, 3), legend=True, fontsize=10, colormap=conf['tmc']['colormap'], width=0.5)
    ax.set_xlabel(conf['tmc']['x_axis_title'], fontsize=10)
    ax.set_xticklabels(ax.get_xticklabels(),rotation=0)
    ax.set_yticks(conf['tmc']['y_tick_values']) 
    ax.set_yticklabels(conf['tmc']['y_tick_labels'])
    ax.set_ylabel(conf['tmc']['y_axis_title'], fontsize=10)
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