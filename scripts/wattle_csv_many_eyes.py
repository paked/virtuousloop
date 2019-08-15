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

def wattle_csv_many_eyes():
    cfg = f.config_exists()

    # print message to console - complete!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # organising the files for uploading to wattle
    # print message to console
    f.pnt_info(c.msg["console_wattle"])

    # get the list of students
    f.load_tsv('data_tutor')

    # load data and create list of teams
    teams=f.load_tsv('students')
    teams.drop_duplicates(subset=['projectteam'], keep='first', inplace=True)
    for i, row in teams.iterrows():
        this_team = row['projectteam']
        # cp pdf to secret here
        file_from = c.d['pdf'] + this_team + ".pdf"
        file_to = c.d['upload'] + this_team + ".pdf"
        copyfile(file_from, file_to)

    f.load_tsv('students')
    students=f.filter_row('students', 'role', 'Student')


    # loop through each row and create a secret for each student
    for i, row in students.iterrows():
        user = row['user']
        role = row['role']
        if role != 'student':
            project_team = row['projectteam']
            shadow_team = row['shadowteam']

            comment = "<ul><li><a href=\"" + cfg['assignment']['feedback_url'] + "/" + str(project_team) + ".pdf\">PDF Feedback for" + str(project_team) + "</a></li><li><a href=\"" + cfg['assignment']['feedback_url'] + "/" + str(shadow_team) + ".pdf\">PDF Feedback for" + str(shadow_team) + "</a></li></ul>"

            # update the df
            students.at[i,'feedback'] = comment


    # print message to console - final csv for upload
    f.pnt_info(c.msg['console_upload'])

    # create an output file
    out=students[['user','feedback']]
    out.to_csv(c.f['wattle'], index=False)



    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
