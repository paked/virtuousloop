#!/usr/bin/env python3
# python ./scripts/11_load_data.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''runs the feedback files based on the settings in app_config.yml'''

import config as c
import functions as f
from load_data import load_data
from load_data import make_json
from feedback_marks import feedback_marks
from feedback_tmc import feedback_tmc
from wattle_csv import wattle_csv
from analysis_marks import analysis_marks
from feedback_many_eyes import feedback_many_eyes
from analysis_many_eyes import analysis_many_eyes
from wattle_csv_many_eyes import wattle_csv_many_eyes
from feedback_course import feedback_course

cfg = f.load_config()

# process the columns needed to run the scripts
load_data()

if cfg['feedback_type']['many_eyes']:
    print(cfg['feedback_type']['many_eyes'])
    feedback_tmc()
    feedback_many_eyes()
    if cfg['feedback_type']['analysis']:
        analysis_many_eyes()
    wattle_csv_many_eyes()

else:
    if cfg['feedback_type']['marks'] and cfg['feedback_type']['tmc']:
        f.pnt_fail(c.msg['console_marks_tmc_conflict'])

    if cfg['feedback_type']['marks']:
        feedback_marks()

    if cfg['feedback_type']['tmc']:
        feedback_tmc()

    if cfg['feedback_type']['analysis']:
        analysis_marks()

    if cfg['feedback_type']['wattle']:
        wattle_csv()

    if cfg['feedback_type']['course']:
        feedback_course()

    if cfg['feedback_type']['json']:
        make_json()
