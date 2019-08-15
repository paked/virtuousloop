#!/usr/bin/env python3
# python ./scripts/config.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''is a module that stores values for the scripts'''
# NOTE: there should be no need to adjust any of the values in this file


d = {
    "feedback": "./feedback/",
    "upload": "./feedback/upload/",
    "archive": "./feedback/archive/",
    "charts": "./feedback/archive/charts/",
    "rubric": "./feedback/archive/rubrics/",
    "yaml": "./feedback/archive/yaml/",
    "css": "./feedback/archive/css/",
    "nlp": "./feedback/archive/nlp/",
    "json": "./feedback/archive/json/",
    "md": "./feedback/archive/md/",
    "pdf": "./feedback/archive/pdf/",
    "html": "./feedback/archive/html/",
    # "tmc_anon": "./feedback/tmc_anonymous/",
    # "tmc_conf": "./feedback/tmc_confidential/",
    # "tmc_chart": "./feedback/tmc/chart/",
    # "tmc_anon_md": "./feedback/tmc/anonymous/md/",
    # "tmc_conf_md": "./feedback/tmc/confidential/md/",
    "files": "./files/",
    "scales": "./files/scales/",
}

f = {
    "students": "./files/students.csv",
    "marks": "./files/marks.csv",
    "crit_levels": "./files/crit_levels.csv",
    "data_tmc": "./files/data_tmc.csv",
    "fields": "./files/fields.csv",
    "data_client": "./files/data_client.csv",
    "data_self": "./files/data_self.csv",
    "data_shadow": "./files/data_shadow.csv",
    "data_tutor": "./files/data_tutor.csv",
    "data_conv": "./files/data_conv.csv",
    "app_config": "./files/app_config.yml",
    "wattle": "./feedback/wattle_upload.csv",
    "json": "./feedback/wattle/database.json",
    "feedack_course": "./files/feedback_course.csv",
}

t = {
    "students": "./files/students.tsv",
    "marks": "./files/marks.tsv",
    "wattle": "./feedback/wattle_upload.tsv",
    "crit_levels": "./files/crit_levels.tsv",
    "data_tmc": "./files/data_tmc.tsv",
    "fields": "./files/fields.tsv",
    "data_client": "./files/data_client.tsv",
    "data_self": "./files/data_self.tsv",
    "data_shadow": "./files/data_shadow.tsv",
    "data_tutor": "./files/data_tutor.tsv",
    "data_conv": "./files/data_conv.tsv",
    "feedack_course": "./files/feedback_course.tsv",
}

df = {
    "students": "students_df",
    "marks": "marks_df",
    "wattle": "wattle_df",
    "crit_levels": "crit_levels_df",
    "data_tmc": "data_tmc_df",
    "fields": "fields_df",
    "marker": "marker_df",
    "data_client": "data_client_df",
    "data_self": "data_self_df",
    "data_shadow": "data_shadow_df",
    "data_tutor": "data_tutor_df",
    "data_conv": "data_conv_df",
    "feedack_course": "feedback_course_df",
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


