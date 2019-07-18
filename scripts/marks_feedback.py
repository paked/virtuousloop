#!/usr/bin/env python3
# python ./scripts/11_load_data.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the marks spreadsheet into pdf feedback'''

import os
import csv
import pandas as pd
import yaml
from shutil import copyfile
from pathlib import Path
import config as c
import functions as f
import pypandoc
from weasyprint import HTML


def marks_feedback():
    
    # check that config exists
    conf=f.config_exists()
    
    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])
    
    # load in tsvs of needed fields
    fields=f.load_tsv('fields')
    marks=f.load_tsv('marks')
    crit_levels=f.load_tsv('crit_levels')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields', 'field', 'crit_')
    comm=f.filter_row('fields', 'field', 'comment_')

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])
    
    # create distribution charts for later
    if conf['crit_display']['graph'] == "true":
        stats=f.make_crit_list(crit)
        f.make_crit_chart(crit, stats)

    #iterate through the marks file
    for i, m_row in marks.iterrows():

        # decide whether to use the list_team or list_name field
        if conf['feedback_type']['group'] == 'true':
            this_record = m_row['list_team']
        else:
            this_record = m_row['user']
            this_record_all = m_row['list_name']

        # define the out files
        # note that the pdf will be copied as out in wattle_csv.py
        this_out = c.d['out'] + this_record + '.md'
        this_pdf = c.d['out'] + this_record + '.pdf'

        # display a progress bar in the console
        # total for progress bar comes from marks.shape[0]
        f.progress_bar(i, marks.shape[0], this_record)
                

        #open up a file to print to
        with open(this_out, 'w') as out:
            
            # create the pandoc header
            if conf['feedback_type']['group'] == 'true':
                f.pandoc_header(out, this_record)
            else:
                f.pandoc_header(out, this_record_all)

            if (conf['crit_display']['text'] == "true") or (conf['crit_display']['scale'] == "true") or (conf['crit_display']['graph'] == "true"):
                # start with indicator title and notes
                print("## " + conf['pdf_messages']['indicator_title'] + "{-}\n\n", file=out)
                print(conf['pdf_messages']['indicator_note'] + "\n\n", file=out)

            #loop through the crit columns
            for j, row in crit.iterrows():

                if (conf['crit_display']['text'] == "true") or (conf['crit_display']['scale'] == "true") or (conf['crit_display']['graph'] == "true"):
                    f.print_results_header('crit', row, m_row, out)

                if conf['crit_display']['text'] == "true":
                    f.print_results_text('crit', row, m_row, out)
                if conf['crit_display']['scale'] == "true":
                    f.print_results_scale('crit', row, m_row, out)
                if conf['crit_display']['graph'] == "true":
                    f.print_results_graph('crit', row, m_row, out)

            # loop through the comment columns
            for j, row in comm.iterrows():
                f.print_results_header('comm', row, m_row, out)
                f.print_results_text('comm', row, m_row, out)

            if conf['crit_display']['rubric'] == "true":
                print("# " + conf['pdf_messages']['rubric_title'] + "{-}\n\n", file=out)
                print(conf['pdf_messages']['rubric_note'] + "\n", file=out)
                f.print_results_rubric(out, m_row, this_record)
                print("\n", file=out)


        # use the anu_cecs.latex template
        pdoc_args = ['--template=./includes/pdf/anu_cecs.latex']
        # convert to pdf
        output = pypandoc.convert_file(this_out, to='pdf', format='md', outputfile=this_pdf, extra_args=pdoc_args)


    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
