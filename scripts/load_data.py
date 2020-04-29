#!/usr/bin/env python3
# python ./scripts/11_load_data.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''runs checks'''

import os
import glob
from pathlib import Path
import config as c
import functions as f

def load_data():
    '''load and clean all the csvs in the files directory'''

    cfg = f.load_config()

    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))
    f.pnt_info(c.msg["console_loading"])
    f.make_directories(c.d)

    # load in all csvs in the files dir
    glob.glob('./files/*.csv')
    for file in glob.glob('./files/*.csv'):
        this_csv = Path(file).stem
        this_rename = cfg['load_file'][this_csv]['rename']
        this_required = cfg['load_file'][this_csv]['required']
        this_index = cfg['load_file'][this_csv]['index']
        this_expected = cfg['load_file'][this_csv]['expected']

        f.load_csv(this_csv)

        # if this_csv == 'data_client':
            # remove first two lines of the qualtrics default csv

        if this_csv == 'feedback_course':
            c.df[this_csv]['tutor_name'] = c.df[this_csv]['tutor'].str.replace(' ', '_')

        if this_csv == 'fields':
            f.col_to_lower(this_csv, "field")

        if this_rename:
            f.rename_header(this_csv, this_rename)
        if this_csv == 'marks':
            c.df[this_csv]['marker_name'] = c.df[this_csv]['marker'].str.replace(' ', '_')
            if not cfg['feedback_type']['group']:
                c.df[this_csv][['user', 'name']] = c.df[this_csv]['list_name'].str.split('\s+-\s+', expand=True)
        if this_index:
            f.check_for_duplicates(this_csv, this_index)
        if this_required:
            f.check_for_empty_cells(this_csv, this_required)
        if this_expected == "crit":
            f.check_for_columns(this_csv)
        elif this_expected == "labels":
            f.check_for_labels(this_csv)

        f.save_tsv(this_csv)

    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))


def make_json():
    '''make a json file for the team'''

    f.load_tsv('students')

    teams = c.df['students'].groupby(['group']).count().reset_index()
    max_member_count = teams['user'].max()

    c.df['students'].dropna(how='any', subset=['user'], inplace=True)

    # add a column with user - first last
    for row in c.df['students'].itertuples():
        def list_name(row):
            return str(row.user) + " - " + str(row.firstname) + " " + str(row.lastname) 
        c.df['students']['list_name'] = c.df['students'].apply(list_name, axis=1)

    # create a list of teams to iterate through
    team_list = f.create_list(teams, "group")

    with open(c.f['json'], 'w') as out:
        for team in team_list:
            # get just the members of the team
            this_team_df = f.filter_row('students', 'group', team)
            print("\'" + team + "\': ", file=out, end='')
            this_team_list = [''] * max_member_count

            for i, row in enumerate(this_team_df.itertuples()):
                this_team_list[i] = row.list_name
            print(str(this_team_list) + ",", file=out)

    # remove the final comma
    with open(c.f['json'], 'rb+') as out:
        out.seek(-2, os.SEEK_END)
        out.truncate()
