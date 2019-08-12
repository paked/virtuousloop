#!/usr/bin/env python3
# python ./scripts/feedback_tmc.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the data_tmc csv into pdf feedback'''

import os
import csv
import config as c
import functions as f
import pandas as pd
import yaml
import shutil
from shutil import copyfile
from pathlib import Path
import pypandoc
from weasyprint import HTML
import itertools
from pandas import DataFrame
import matplotlib.pyplot as plt
import subprocess
import re

# silence matplot warnings
plt.rcParams.update({'figure.max_open_warning': 0})

# main loop
def feedback_tmc():
    
    #check that config exists
    cfg=f.config_exists()

    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])
    
    # load data and create list of teams
    teams=f.load_tsv('data_tmc')
    teams.drop_duplicates(subset=['list_team'], keep='first', inplace=True)
    teams=teams['list_team']

    # load data and translate the written labels into values
    data_tmc=f.load_tsv('data_tmc')
    data_tmc.replace(cfg['tmc_chart']['find_labels'], cfg['tmc_chart']['replace_values'], inplace=True) 
    
    # create a list of column headers for team member contributions
    # sort the list from TM1 to TMx
    # add the username field as first entry of the list
    # create a parallel list of column headers for IDs
    tm_cols_tmc = [col for col in data_tmc.columns if 'contribution' in col]
    tm_cols_tmc.sort()
    tm_cols_tmc.insert(0,'username')
    tm_cols_id = [w.replace('contribution', 'id') for w in tm_cols_tmc]

    # for each team 
    for team in teams: 

        # display a progress bar in the console
        # total for progress bar comes from marks.shape[0]
        f.progress_bar(1, teams.shape[0], team)

        # get the tmc values matching the team
        # only take the first row of tm_cols_id as the list
        # change the first entry to 'reviews'
        this_data=f.filter_row('data_tmc', 'list_team', team)
        team_header=this_data[tm_cols_id].values.tolist()[0]
        team_header[0]='reviews'

        # get the tmc values matching the team
        # take tm_cols_tmc as the list
        team_data=this_data[tm_cols_tmc].values.tolist()
        
        # assemble the lists into the confidential df
        # strip the names of the reviewed for the anonymous version, transpose
        # transpose the conf_df
        this_conf_df=DataFrame.from_records(team_data, columns=team_header).set_index('reviews').dropna(axis=1, how='all')
        this_anon_df=this_conf_df.rename(columns=lambda x: re.sub(' - .*','',x)).T
        this_anon_df=this_anon_df.rename(columns=lambda x: re.sub('u.*',cfg['tmc_chart']['anon_legend'],x))
        this_conf_df=this_conf_df.T

        # get the shape of the dataframe to show the number of submissions
        shape=this_anon_df.shape

        this_anon_df['average'] = this_anon_df.mean(axis=1)
        this_conf_df['average'] = this_conf_df.mean(axis=1)

        # make the charts
        f.make_tmc_chart(this_anon_df, c.d['tmc_chart'] + team + "_anon.pdf")
        f.make_tmc_chart(this_conf_df, c.d['tmc_chart'] + team + "_conf.pdf")

        format_feedback(team, 'conf', shape, this_data)
        format_feedback(team, 'anon', shape, this_data)

    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))

# print feedback loop
def format_feedback(team, kind, shape, dataframe):
    cfg=f.config_exists()

    this_out=c.d['tmc_' + kind] + team

    with open(this_out + ".md", 'w') as out:

        # print pandoc header
        f.pandoc_header(out, team)

        # print graph
        this_chart=c.d['tmc_chart'] + team + "_" + kind + ".pdf"
        this_chart_path=Path(this_chart)
        
        # check that a chart has been generated
        # if so, print the title and caption too
        if this_chart_path.is_file():

            print("\n\n## " + cfg['tmc_pdf']['eval_header'] + "{-}\n\n", file=out)
            if ( cfg['tmc_pdf']['team_count_message'] == "true" ):
                print("**" + str(shape[1]) + "**" + " out of **" + str(shape[0]) + "** " + cfg['tmc_pdf']['count_message'] + "\n\n", file=out)

            print('![](' + this_chart + ')\n\n', file=out)
            print( cfg['tmc_pdf']['tmc_chart_caption'] + "\n\n", file=out )
        
        # print the comments for the team
        print("## " + cfg['pdf_messages']['tmc_title'] + "{-}\n\n", file=out)
        for i, df_row in dataframe.iterrows():
            # if the field is empty
            if ( str(df_row['teamcomments']) == "nan"):
                # print confidential and anonymous
                if ( kind == 'conf'):
                    print("### " + df_row['user'] + " (" + df_row['username'] + ")" + " {-}\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                else:
                    print("### " + cfg['tmc_pdf']['member_header'] + " {-}\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
            else:
                # print confidential and anonymous
                if ( kind == 'conf'):
                    print("### " + df_row['user'] + " (" + df_row['username'] + ")" + " {-}\n\n" + str(df_row['teamcomments']) + "\n\n", file=out)
                else:
                    print("### " + cfg['tmc_pdf']['member_header'] + " {-}\n\n" + str(df_row['teamcomments']) + "\n\n", file=out)

        # print confidential comments
        if ( kind == 'conf'):
            print("## " + cfg['pdf_messages']['tmc_confidential'] + "{-}\n\n", file=out)
            for i, df_row in dataframe.iterrows():
                # try encoding utf8
                if ( df_row['confidentialcomments'] == "nan"):
                    print("### " + df_row['user'] + " (" + df_row['username'] + ")" + " {-}\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                else:
                    print("### " + df_row['user'] + " (" + df_row['username'] + ")" + " {-}\n\n" + str(df_row['confidentialcomments']) + "\n\n", file=out)

    # convert md to pdf using the shell
    f.pandoc_pdf(this_out)

    # archive the md files
    source = c.d['tmc_' + kind] + team + '.md'
    dest = c.d['tmc_' + kind + '_md'] + team + '.md'
    shutil.move(source, dest)
