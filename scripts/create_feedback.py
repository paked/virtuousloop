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
from feedback_marks import feedback_marks
from feedback_tmc import feedback_tmc
from wattle_csv import wattle_csv
from analysis_marks import analysis_marks
from feedback_many_eyes import feedback_many_eyes
from wattle_csv_many_eyes import wattle_csv_many_eyes



cfg = f.config_exists()

# process the columns needed to run the scripts
load_data()

if (cfg['feedback_type']['many_eyes'] == 'true'):
	#feedback_tmc()
	#feedback_many_eyes()
	wattle_csv_many_eyes()

else:
	if (cfg['feedback_type']['marks'] == 'true') and (cfg['feedback_type']['tmc'] == 'true'):
		f.pnt_fail(c.msg['console_marks_tmc_conflict'])

	if (cfg['feedback_type']['marks'] == 'true'):
		# extract the crit/comment fields from the marks file
		feedback_marks()

	if (cfg['feedback_type']['tmc'] == 'true'):
		# run the tmc module
		feedback_tmc()

	if (cfg['feedback_type']['analysis'] == 'true'):
		analysis_marks()

	# create csv to upload to wattle
	if (cfg['feedback_type']['wattle'] == 'true'):
		wattle_csv()