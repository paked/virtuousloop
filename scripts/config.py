#!/usr/bin/env python3
# python ./scripts/config.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''is a module that stores values for the scripts'''
# NOTE: there should be no need to adjust any of the values in this file


d = {
    "feedback_dir": "./feedback/"
    "out": "./feedback/out/",
    "pdf": "./feedback/pdf/",
    "graphs": "./feedback/graphs/",
    "scales": "./files/scales/",
    "rubric": "./feedback/rubrics/",
    "tmc": "./feedback/tmc/",
}

tmc = {
    "anon": "./feedback/anon/",
    "conf": "./feedback/conf/",
}

f = {
    "students": "./files/students.csv",
    "marks": "./files/marks.csv",
    "wattle": "./feedback/wattle.csv",
    "crit_levels": "./files/crit_levels.csv",
    "data_tmc": "./files/data_tmc.csv",
    "fields": "./files/fields.csv",
    "app_config": "./files/app_config.yml"

}

t = {
    "students": "./files/students.tsv",
    "marks": "./files/marks.tsv",
    "wattle": "./feedback/wattle.tsv",
    "crit_levels": "./files/crit_levels.tsv",
    "data_tmc": "./files/data_tmc.tsv",
    "fields": "./files/fields.tsv",
}

df = {
    "students": "students_df",
    "marks": "marks_df",
    "wattle": "wattle_df",
    "crit_levels": "crit_levels_df",
    "data_tmc": "data_tmc_df",
    "fields": "fields_df"
}

h = {
    "wkhtml_header": "./includes/pdf/header.html",
    "wkhtml_footer": "./includes/pdf/footer.html",
}

msg = {
    "console_wattle": "organising the files for wattle upload..",
    "console_duplicates": "checking for duplicates..",
    "console_secrets": "creating secrets for each student..",
    "console_upload": "creating upload file..",
    "console_start": "STARTING...",
    "console_complete": "COMPLETE...",
    "console_loading": "loading files into the scripts..",
    "console_app_config_check": "checking that ./files/app_config.yml exists..",
    "console_app_config_fail": "Can't locate ./files/app_config.yml. Please find it. The script will fail.",
    "console_creating_feedback_files": "Creating feedback files..",
    "console_marks_tmc_conflict": "Both Marks and TMC are true is ./files/app_config.yml. Only one can be 'true'. The script will probably fail.",
    "check_dupes": "there are duplicates in the csv: ",
    "fail_warn": "Please find it. The script will fail.",
}


