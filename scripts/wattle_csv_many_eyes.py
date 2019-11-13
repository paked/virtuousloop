#!/usr/bin/env python3
# python ./scripts/21_wattle_cs.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''creates a file ready to upload to Wattle'''

import os
from shutil import copyfile
import pandas as pd
import config as c
import functions as f

def wattle_csv_many_eyes():
    cfg = f.load_config()

    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))
    f.pnt_info(c.msg["console_wattle"])
    f.load_tsv('data_tutor')

    teams = f.load_tsv('students')
    teams.drop_duplicates(subset=['group'], keep='first', inplace=True)
    for i, row in teams.iterrows():
        this_team = row['group']
        # cp pdf to secret here
        file_from = c.d['pdf'] + this_team + "_" + cfg['assignment']['assignment_short'] + "_audit_anon.pdf"
        file_to = c.d['upload'] + this_team + "_" + cfg['assignment']['assignment_short'] + ".pdf"
        copyfile(file_from, file_to)

    f.load_tsv('students')
    students = f.filter_row('students', 'role', 'Student')
    user_list = []
    comment_list = []

    for i, row in students.iterrows():
        user = row['user']
        role = row['role']
        project_team = row['group']
        team_row = f.filter_row('data_tutor', 'team', project_team)
        if not team_row.empty:
            team_performance = team_row.iloc[0]['suggestedindicator']
        else:
            team_performance = "TBA"

        if role != 'student':
            project_team = row['group']
            shadow_team = row['shadowteam']
            comment = "Your Team's Progress Indicator:"
            comment += "<ul><li><strong>" + team_performance + "</strong></li></ul>"
            comment += "Feedback for Your Teams:"
            comment += "<ul><li><a href=\"" + cfg['assignment']['feedback_url'] + "/" + str(project_team) + ".pdf\">PDF Feedback for your team: " + str(project_team) + "</a></li>"
            comment += "<li><a href=\"" + cfg['assignment']['feedback_url'] + "/" + str(shadow_team) + ".pdf\">PDF Feedback for shadow team: " + str(shadow_team) + "</a></li></ul>"

            user_list.append(user)
            comment_list.append(comment)

    f.pnt_info(c.msg['console_upload'])

    this_out = pd.DataFrame()
    this_out['users']=user_list
    this_out['feedback']=comment_list
    this_out.to_csv(c.f['wattle'], index=False)

    f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))
