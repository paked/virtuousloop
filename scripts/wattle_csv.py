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
    cfg = f.load_config()

    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))
    f.pnt_info(c.msg["console_wattle"])

    f.load_tsv('students')
    f.load_tsv('marks')

    if not cfg['feedback_type']['group']:
        f.pnt_info(c.msg['console_secrets'])

        for i, row in c.df['marks'].iterrows():
            user = row['user']
            secret = hashlib.sha1(row['user'].encode('utf-8')).hexdigest()
            secret_file = user + "-" + secret + ".pdf"

            comment = "<a href=\"" + cfg['assignment']['feedback_url'] + "/" + user + "-" + secret + ".pdf\">PDF Feedback</a>"
            c.df['marks'].at[i,'secret'] = comment
            
            file_from = c.d['pdf'] + user + ".pdf"
            file_to = c.d['upload'] + secret_file
            copyfile(file_from, file_to)
        marks_out=c.df['marks'][['user','grade_final','secret']]
        wattle_out = marks_out.merge(c.df['students'], on='user', how='left')[['user','grade_final','secret']]

    else:
        for i, row in c.df['marks'].iterrows():
            user = row['user']
            group = row['list_team']

            comment = "<a href=\"" + cfg['assignment']['feedback_url'] + "/" + group + ".pdf\">PDF Feedback for " + group + "</a>"
            c.df['marks'].at[i,'secret'] = comment
            
            file_from = c.d['pdf'] + group + ".pdf"
            file_to = c.d['upload'] + group + ".pdf"
            copyfile(file_from, file_to)

        marks_out=c.df['marks'][['list_team','grade_final','secret']]
        wattle_out = marks_out.merge(c.df['students'], left_on='list_team', right_on='group', how='left')[['user','grade_final','secret','group']]
        print(wattle_out)

    f.pnt_info(c.msg['console_upload'])
    wattle_out.to_csv(c.f['wattle'], index=False)
    f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))
