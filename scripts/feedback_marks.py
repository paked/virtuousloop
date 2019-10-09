#!/usr/bin/env python3
# python ./scripts/feedback_marks.py
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
import subprocess


def feedback_marks():
    
    # check that config exists
    cfg=f.config_exists()
    
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
    if cfg['crit_display']['graph'] == "true":
        stats=f.make_crit_list(crit, marks)
        f.make_crit_chart(crit, stats, "na")

    #iterate through the marks file
    for i, m_row in marks.iterrows():

        # decide whether to use the list_team or list_name field
        if cfg['feedback_type']['group'] == 'true':
            this_record = m_row['list_team']
        else:
            this_record = m_row['user']
            this_record_all = m_row['list_name']

        # display a progress bar in the console
        print(this_record)
                
        # create the pandoc header
        with open(c.d['yaml'] + this_record + '.yaml', 'w') as out:
            if cfg['feedback_type']['group'] == 'true':
                f.pandoc_yaml(out, this_record)
            else:
                f.pandoc_yaml(out, this_record_all)

        # create the pandoc header
        with open(c.d['css'] + this_record + '.css', 'w') as out:
            if cfg['feedback_type']['group'] == 'true':
                f.pandoc_css(out, this_record, 'anon')
            else:
                f.pandoc_css(out, this_record_all, 'anon')

        #open up a file to print to
        with open(c.d['md'] + this_record + '.md', 'w') as out:

            if (cfg['crit_display']['text'] == "true") or (cfg['crit_display']['scale'] == "true") or (cfg['crit_display']['graph'] == "true"):
                # start with indicator title and notes
                print("## " + cfg['pdf_messages']['indicator_title'] + "{-}\n\n", file=out)
                print(cfg['pdf_messages']['indicator_note'] + "\n\n", file=out)

            #loop through the crit columns
            for j, row in crit.iterrows():

                # display the fields according to app_config
                if (cfg['crit_display']['text'] == "true") or (cfg['crit_display']['scale'] == "true") or (cfg['crit_display']['graph'] == "true"):
                    f.print_results_header('crit', row, m_row, out)
                if cfg['crit_display']['text'] == "true":
                    f.print_results_text('crit', row, m_row, out)
                if cfg['crit_display']['scale'] == "true":
                    f.print_results_scale('crit', row, m_row, out)
                if cfg['crit_display']['graph'] == "true":
                    f.print_results_graph('crit', row, m_row, out)

            # loop through the comment columns
            for j, row in comm.iterrows():
                f.print_results_header('comm', row, m_row, out)
                f.print_results_text('comm', row, m_row, out)

            if cfg['crit_display']['rubric'] == "true":
                print("# " + cfg['pdf_messages']['rubric_title'] + "{-}\n\n", file=out)
                print(cfg['pdf_messages']['rubric_note'] + "\n", file=out)
                f.print_results_rubric(out, m_row, this_record)
                print("\n", file=out)

        # convert md to pdf using the shell
        f.pandoc_html_single(this_record)

        if cfg['crit_display']['rubric'] == "true":

            files = [c.d['rubric'] + this_record + ".html"]
            with open(c.d['html'] + this_record + '.html', 'a') as outfile:
                for fname in files:
                    with open(fname) as infile:
                        outfile.write(infile.read())

        f.pandoc_pdf(this_record)
 
    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
