#!/usr/bin/env python3
# python ./scripts/11_load_data.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''runs the feedback files'''

import config as c
import functions as f
from load_data import load_data
from marks_feedback import marks_feedback
from team_member_contribution import team_member_contribution
from wattle_csv import wattle_csv

conf = f.config_exists()

# process the columns needed to run the scripts
load_data()

# if (conf['feedback_type']['marks'] == 'true') and (conf['feedback_type']['tmc'] == 'true'):
# 	f.pnt_fail(c.msg['console_marks_tmc_conflict'])

# if (conf['feedback_type']['marks'] == 'true'):
# 	# extract the crit/comment fields from the marks file
# 	marks_feedback()

if (conf['feedback_type']['tmc'] == 'true'):
	# extract the crit/comment fields from the marks file
	team_member_contribution()

# # create csv to upload to wattle
# wattle_csv()