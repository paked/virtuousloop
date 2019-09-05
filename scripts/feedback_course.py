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


def feedback_course():
    
    # check that config exists
    cfg=f.config_exists()
    
    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])
    
    # load in tsvs of needed fields
    tutors=f.load_tsv('feedback_course')
    tutors.drop_duplicates(subset=['tutor_name'], keep='first', inplace=True)

    tutor_list=[]
    for i, row in tutors.iterrows():
        this_tutor = row['tutor_name']
        tutor_list.append(this_tutor)
    print(tutor_list)

    feedback_course_df=f.load_tsv('feedback_course')

    crit_levels=f.load_tsv('fields_course')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields_course', 'field', 'crit_')
    comm=f.filter_row('fields_course', 'field', 'comment_')

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])

    for tutor in tutor_list:
        print(tutor)
        this_tutor_df=feedback_course_df[feedback_course_df['tutor_name'].str.contains(tutor)]
         
        with open(c.d['yaml'] + tutor + '.yaml', 'w') as out:
        # create the pandoc header
            f.pandoc_yaml(out, tutor)
            
        with open(c.d['css'] + tutor + '.css', 'w') as out:
        # create the pandoc header
            f.pandoc_css(out, tutor, 'class')
            
        #open up a file to print to
        with open(c.d['md'] + tutor + '_anon.md', 'w') as out:

            # loop through the comment columns
            for j, row in comm.iterrows():
                this_field=str(row['field'])
                this_description=str(row['description'])
                if this_field != 'comment_confidential':
                    print("\n\n## " + this_description + "\n\n", file=out)

                    for i, i_row in this_tutor_df.iterrows():
                        this_text=str(i_row[this_field])
                        if ( this_text != "" ):
                            print("**Student Comment**\n\n" + this_text + "\n\n", file=out)

        #open up a file to print to
        with open(c.d['md'] + tutor + '_conf.md', 'w') as out:

            # loop through the comment columns
            for j, row in comm.iterrows():
                this_field=str(row['field'])
                this_description=str(row['description'])

                print("\n\n## " + this_description + "\n\n", file=out)

                for i, i_row in this_tutor_df.iterrows():
                    this_text=str(i_row[this_field])
                    this_user=str(i_row['user'])
                    if ( this_text != "nan" ):
                        print("**" + this_user + "**\n\n" + this_text + "\n\n", file=out)

        f.pandoc_html(tutor + "_anon", tutor, 'anon')
        f.pandoc_html(tutor + "_conf", tutor, 'conf')

        f.pandoc_pdf(tutor + "_anon", tutor, 'anon')
        f.pandoc_pdf(tutor + "_conf", tutor, 'conf')


    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
