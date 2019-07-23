#!/usr/bin/env python3
# python ./scripts/feedback_tmc.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the data_tmc csv into pdf feedback'''

import os
import csv
import pandas as pd
import yaml
from shutil import copyfile
from pathlib import Path
import config as c
import functions as f
import pypandoc
from weasyprint import HTML
import itertools
from pandas import DataFrame
import re
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.max_open_warning': 0})


def feedback_tmc():
    
    #check that config exists
    conf=f.config_exists()

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
    data_tmc.replace(conf['tmc']['find_labels'], conf['tmc']['replace_values'], inplace=True) 
    
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
        this_anon_df=this_anon_df.rename(columns=lambda x: re.sub('u.*',conf['tmc']['anon_legend'],x))
        this_conf_df=this_conf_df.T

        # get the shape of the dataframe to show the number of submissions
        shape=this_anon_df.shape
        this_anon_df['average'] = this_anon_df.mean(axis=1)
        this_conf_df['average'] = this_conf_df.mean(axis=1)

        # set the out files
        tmc_conf_out = c.d['tmc'] + team + "_conf.pdf"
        tmc_anon_out = c.d['tmc'] + team + "_anon.pdf"

        # make the charts
        f.make_tmc_chart(this_conf_df, tmc_conf_out)
        f.make_tmc_chart(this_anon_df, tmc_anon_out)

        this_out=c.tmc['anon'] + team + ".md"
        this_pdf=c.tmc['anon'] + team + ".pdf"        
        with open(this_out, 'w') as out:

            f.pandoc_header(out, team)

            print("Peer evaluation of contribution by team members\n\n", file=out)
            print("*" + str(shape[1]) + "*" + " out of *" + str(shape[0]) + "* team members submitted reviews.\n\n", file=out)
            print('![](./feedback/tmc/' + team + '_anon.pdf)\n\n', file=out)
            header=conf['pdf_messages']['tmc_title']
            print("## " + header + "{-}\n\n", file=out)
            for i, df_row in this_data.iterrows():
                # try encoding utf8
                if ( str(df_row['teamcomments']) == "nan"):
                    print("### Team member {-}\n\nNo comments\n\n", file=out)
                else:
                    print("### Team member {-}\n\n" + str(df_row['teamcomments']) + "\n\n", file=out)

        HTML(this_out).write_pdf(this_pdf)

        this_out=c.tmc['conf'] + team + ".md"
        this_pdf=c.tmc['conf'] + team + ".pdf"        
        with open(this_out, 'w') as out:

            f.pandoc_header(out, team)
            print("Peer evaluation of contribution by team members\n\n", file=out)
            print("*" + str(shape[1]) + "*" + " out of *" + str(shape[0]) + "* team members submitted reviews.\n\n", file=out)
            print('![](./feedback/tmc/' + team + '_anon.pdf)\n\n', file=out)
            header=conf['pdf_messages']['tmc_title']
            print("## " + header + "{-}\n\n", file=out)

            for i, df_row in this_data.iterrows():
                # try encoding utf8
                if ( df_row['teamcomments'] == "nan"):
                    print("###" + df_row['username'] + "Team member {-}\n\nNo comments\n\n", file=out)
                else:
                    print("###" + df_row['username'] + " (Team member) {-}\n\n" + str(df_row['teamcomments']) + "\n\n", file=out)
            
            header=conf['pdf_messages']['tmc_confidential']
            print("## " + header + "{-}\n\n", file=out)
            for i, df_row in this_data.iterrows():
                # try encoding utf8
                if ( df_row['confidentialcomments'] == "nan"):
                    print("### " + df_row['username'] + "Team member {-}\n\nNo comments\n\n", file=out)
                else:
                    print("### " + df_row['username'] + " (Team member){-}\n\n" + str(df_row['confidentialcomments']) + "\n\n", file=out)
            

        HTML(this_out).write_pdf(this_pdf)

        # # use the anu_cecs.latex template
        # pdoc_args = ['--pdf-engine', '/usr/bin/xelatex']
        # # convert to pdf
        # output = pypandoc.convert_file(this_out, to='md', format='md', outputfile=this_out, extra_args=['--pdf-engine', '/usr/bin/xelatex'])

        # print message to console - complete!
        f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))

