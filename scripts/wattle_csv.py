#!/usr/bin/env python3
# python ./scripts/21_wattle_cs.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''creates a file ready to upload to Wattle'''

import os
import csv
import pandas as pd
import yaml
import hashlib
from shutil import copyfile
import config as c
import functions as f

def wattle_csv():
    
    try:
        config = open('./files/app_config.yml')
    except IOError:
        f.pnt_fail("Can't locate ./files/app_config.yml. Please find it. The script will fail.")
    else:
        conf = yaml.safe_load(config)

    # print message to console - complete!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # organising the files for uploading to wattle
    # print message to console
    f.pnt_info(c.msg["console_wattle"])

    # get the list of students
    f.load_tsv('students')
    f.load_tsv('marks')

    
    if conf['fields']['marks_field'] == 'list_name':

        # print message to console - creating secrets
        f.pnt_info(c.msg['console_secrets'])

        # loop through each row and create a secret for each student
        for i, row in c.df['marks'].iterrows():
            user = row['user']
            secret = hashlib.sha1(row['user'].encode('utf-8')).hexdigest()
            secret_file = user + "-" + secret + ".pdf"
            comment = "<a href=\"" + conf['assignment']['feedback_url'] + "/" + user + "-" + secret + ".pdf\">PDF Feedback</a>"
            
            # update the df
            c.df['marks'].at[i,'secret'] = comment
            
            # cp pdf to secret here
            file_from = c.d['out'] + user + ".pdf"
            file_to = c.d['pdf'] + secret_file
            copyfile(file_from, file_to)

    elif conf['fields']['marks_field'] == 'list_team':

        # loop through each row and create a secret for each student
        for i, row in c.df['marks'].iterrows():
            user = row['user']
            group = row['list_team']

            comment = "<a href=\"" + conf['assignment']['feedback_url'] + "/" + group + ".pdf\">PDF Feedback for" + group + "</a>"

            # update the df
            c.df['marks'].at[i,'secret'] = comment
            
            # cp pdf to secret here
            file_from = c.d['out'] + group + ".pdf"
            file_to = c.d['pdf'] + group + ".pdf"
            copyfile(file_from, file_to)
    else:
        f.pnt_info(c.msg['console_missing_marks_field'])

    # print message to console - final csv for upload
    f.pnt_info(c.msg['console_upload'])

    # create an output file
    out = c.df['marks'].merge(c.df['students'], on='user')[['user','grade_final','secret']]
    out.to_csv(c.f['wattle'], index=False)



    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
