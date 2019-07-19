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

    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])

    # load in all csvs in the files dir
    glob.glob('./files/*.csv')
    for files in glob.glob('./files/*.csv'):
        this_csv=Path(files).stem
        f.load_csv(this_csv)
        if this_csv == 'students':
            # rename fields
            f.rename_header(this_csv, 'user id', 'user')
            f.rename_header(this_csv, 'first_name', 'first')
            f.rename_header(this_csv, 'Surname', 'last')
            f.check_duplicates(this_csv, 'user')
        elif this_csv == 'marks':
            # rename fields
            f.rename_header(this_csv, 'username', 'marker_id')
            f.rename_header(this_csv, 'user', 'marker_name')
            # split the user - name column in c.df[this_csv]
            c.df[this_csv][['user','name']] = c.df[this_csv]['list_name'].str.split('\s+-\s+', expand=True)
            f.check_duplicates(this_csv, 'user')
        elif this_csv == 'fields':
            # lower fields to match marks.csv lower
            f.col_to_lower(this_csv, 'field')
        elif this_csv == 'crit_levels':
            # rename fields
            f.rename_header(this_csv, 'level', 'index')
        elif this_csv == 'data_tmc':
            # rename fields
            f.rename_header(this_csv, 'teamdropdown', 'list_team')

        #print(c.df[this_csv])
        c.df[this_csv].to_csv(c.t[this_csv], sep='\t', encoding='utf-8', index=False)

    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))