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
    crit_levels=f.load_tsv('crit_levels')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields', 'field', 'crit_')
    comm=f.filter_row('fields', 'field', 'comment_')

    crit_levels_list=[] 
    for i, row in crit_levels.iterrows():
        this_val = str(row['index'])
        crit_levels_list.append(this_val)
    print(crit_levels_list)

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])

    for i, row in crit.iterrows():
        this_crit=row['field']
        this_crit_list=[]
        for tutor in tutor_list:
            this_tutor_df=feedback_course_df[feedback_course_df['tutor_name'].str.contains(tutor)]
            this_tutor_crit=[]
            this_header=[tutor]
            for val in crit_levels_list:
                this_sum=(this_tutor_df[this_crit]==val).sum()
                this_tutor_crit.append(this_sum)
            this_crit_list.append(this_tutor_crit)
            this_crit_this_tutor = pd.DataFrame(this_tutor_crit, columns = this_header, index = crit_levels_list)
            f.make_feedback_chart(this_crit_this_tutor, c.d['charts'] + this_crit + "_" + tutor + ".png")
        this_crit_all_tutors = pd.DataFrame(this_crit_list, columns = crit_levels_list, index=tutor_list)
        this_crit_all_tutors = this_crit_all_tutors.T
        f.make_feedback_chart(this_crit_all_tutors, c.d['charts'] + this_crit + "_all_tutor.png")
  
    with open(c.d['yaml'] + 'all.yaml', 'w') as out:
    # create the pandoc header
        f.pandoc_yaml(out, 'All Tutors')
        
    with open(c.d['css'] + 'all_conf.css', 'w') as out:
    # create the pandoc header
        f.pandoc_css(out, 'Course Feedback', 'class')
    #open up a file to print to
    with open(c.d['md'] + 'all.md', 'w') as out:
        # loop through the comment columns
        print("# Quantitative Feedback{-}\n\n", file=out)
        for i, row in crit.iterrows():
            this_crit=str(row['field'])
            this_text = str(row['description'])
            this_image = c.d['charts'] + this_crit + "_all_tutor.png"
            print("### " + this_text + "{-}\n\n", file=out)
            print("![](../../." + this_image + ")\n\n", file=out)

    confidential_files=[c.d['md'] + 'all.md']

    for tutor in tutor_list:
        print(tutor)
        this_tutor_df=feedback_course_df[feedback_course_df['tutor_name'].str.contains(tutor)]

        with open(c.d['yaml'] + tutor + '.yaml', 'w') as out:
        # create the pandoc header
            f.pandoc_yaml(out, tutor)
            
        with open(c.d['css'] + tutor + '_anon.css', 'w') as out:
        # create the pandoc header
            f.pandoc_css(out, tutor, 'class')
            
        #open up a file to print to
        with open(c.d['md'] + tutor + '_anon.md', 'w') as out:
            # loop through the comment columns
            for i, row in crit.iterrows():
                this_crit=str(row['field'])
                this_text = str(row['description'])
                this_image = c.d['charts'] + this_crit + "_" + tutor + ".png"

                print("### " + this_text + "{-}\n\n", file=out)
                print("![](../../." + this_image + ")\n\n", file=out)
                  
            # loop through the comment columns
            for i, row in comm.iterrows():
                this_field=str(row['field'])
                this_description=str(row['description'])
                if this_field != 'comment_confidential':
                    print("\n\n## " + this_description + "\n\n", file=out)

                    for i, i_row in this_tutor_df.iterrows():
                        this_text=str(i_row[this_field])
                        if ( this_text != "" ):
                            print("**Student Comment**\n\n" + this_text + "\n\n", file=out)

            f.pandoc_html(tutor + "_anon", tutor, 'anon')
            f.pandoc_pdf(tutor + "_anon", tutor, 'anon')

        # def pandoc_html(this_file, this_record, kind):
        # subprocess.call("pandoc -s -t html5 \
        # -c ../../../includes/pdf/single.css \
        # -c ../../." + c.d["css"] + this_record + "_" + kind + ".css \
        # --metadata-file=" + c.d["yaml"] + this_record + ".yaml \
        # --template=./includes/pdf/pandoc_single.html \
        # " + c.d["md"] + this_file + ".md \
        # -o " + c.d["html"] + this_file + ".html", shell=True)

        #open up a file to print to
        with open(c.d['md'] + tutor + '_conf.md', 'w') as out:
            print("\n\n# Feedback for " + tutor + "\n\n", file=out)
            confidential_files.append(c.d['md'] + tutor + '_conf.md')

            # loop through the comment columns
            for i, row in comm.iterrows():
                this_crit=str(row['field'])
                this_text = str(row['description'])
                this_image = c.d['charts'] + this_crit + "_" + tutor + ".png"

                print("\n\n## " + this_description + "\n\n", file=out)

                for i, i_row in this_tutor_df.iterrows():
                    this_text=str(i_row[this_field])
                    this_user=str(i_row['user'])
                    if ( this_text != "nan" ):
                        print("**" + this_user + "**\n\n" + this_text + "\n\n", file=out)
            
    print(confidential_files)
    with open(c.d['md'] + "confidential_feedback.md", 'w') as outfile:
        for fname in confidential_files:
            with open(fname) as infile:
                outfile.write(infile.read())

    f.pandoc_html_toc('confidential_feedback', 'all', 'conf')
    f.pandoc_pdf('confidential_feedback', 'all', 'conf')


    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
