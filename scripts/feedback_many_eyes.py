#!/usr/bin/env python3
# python ./scripts/feedback_many_eyes.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the data_ csvs into pdf feedback'''

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
import subprocess

def feedback_many_eyes():
    
    # check that config exists
    cfg=f.config_exists()
    
    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])
    
    # load in tsvs of needed fields
    fields=f.load_tsv('fields')
    crit_levels=f.load_tsv('crit_levels')

    data_self=f.load_tsv('data_self')
    data_shadow=f.load_tsv('data_shadow')
    data_tutor=f.load_tsv('data_tutor')
    data_client=f.load_tsv('data_client')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields', 'field', 'crit_')
    comm=f.filter_row('fields', 'field', 'comment_')

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])
    
    # load data and create list of teams
    teams=f.load_tsv('students')
    teams.drop_duplicates(subset=['group'], keep='first', inplace=True)

    # create a list of crit for access
    crit_list=[]
    for j, row in crit.iterrows():
         crit_list.append(row['label'])

    # create a df for access for self and shadow
    f.many_eyes_dataframe_sort('data_self')
    f.many_eyes_dataframe_sort('data_shadow')

    self_df=f.load_tsv('data_self_sorted')
    shadow_df=f.load_tsv('data_shadow_sorted')

    # create a df to access for tutor comments
    tutor_df=c.df['data_tutor']
    tutor_df.replace(cfg['audit_chart']['find_labels'], cfg['audit_chart']['replace_values'], inplace=True) 
   
    # create a df to access for client comments
    client_df=c.df['data_client']
    client_df.replace(cfg['audit_chart']['find_client_labels'], cfg['audit_chart']['replace_client_values'], inplace=True) 

    # work through the many eyes data
    for eyes in cfg['many_eyes']['eyes']:
        this_array = 'class_' + eyes + '_ave'
        vars()[this_array]=[]

    # start a list for each eye
    class_self_ave=[]
    class_shadow_ave=[]
    class_tutor_ave=[]
    class_client_ave=[]

    #loop through the crit columns
    for j, row in crit.iterrows():
        class_self_crit_df=self_df[self_df['crit_text'].str.contains(row['label'])]
        class_shadow_crit_df=shadow_df[shadow_df['crit_text'].str.contains(row['label'])]
                
        class_self_ave.append(class_self_crit_df['crit_val'].mean())
        class_shadow_ave.append(class_shadow_crit_df['crit_val'].mean())
        class_tutor_ave.append(tutor_df[row['field']].mean())
        class_client_ave.append(client_df[row['field']].mean())

    # build a df for class averages
    class_ave_df = pd.DataFrame()
    class_ave_df['criterion'] = crit_list
    class_ave_df['self'] = class_self_ave
    class_ave_df['shadow'] = class_shadow_ave
    class_ave_df['tutor'] = class_tutor_ave
    class_ave_df['client'] = class_client_ave
    class_ave_df['class_ave'] = class_ave_df.mean(axis=1)

    class_ave_list = class_ave_df["class_ave"].values

    # create a team list to iterate through
    team_list=[]
    for i, row in teams.iterrows():
        this_team = row['group']
        team_list.append(this_team)

    f.pnt_info(c.msg["console_many_eyes"])

    # for each team 
    for team in team_list: 
        # report to the console
        print(team)

        # create a df for summary stats
        this_team_self_df=self_df[self_df['team'].str.contains(team)]
        this_team_shadow_df=shadow_df[shadow_df['team'].str.contains(team)]
        this_team_tutor_df=tutor_df[tutor_df['team'].str.contains(team)]
        this_team_client_df=client_df[client_df['team'].str.contains(team, na=False)]


        # create lists for the averages
        crit_self_ave=[]
        crit_shadow_ave=[]
        crit_tutor_ave=[]
        crit_client_ave=[]
        
        #loop through the crit columns
        for j, row in crit.iterrows():

            this_team_self_crit_df=this_team_self_df[this_team_self_df['crit_text'].str.contains(row['label'])]
            this_team_shadow_crit_df=this_team_shadow_df[this_team_shadow_df['crit_text'].str.contains(row['label'])]
            # add the mean to the list
            crit_self_ave.append(this_team_self_crit_df['crit_val'].mean())
            crit_shadow_ave.append(this_team_shadow_crit_df['crit_val'].mean())
            crit_tutor_ave.append(this_team_tutor_df[row['field']].mean())

        # deal with empty client df entries
        if this_team_client_df.empty:
            for l, row in crit.iterrows():
                crit_client_ave.append('0')
        else:
            for l, row in crit.iterrows():
                crit_client_ave.append(this_team_client_df[row['field']].mean())

        # create a df for the team to generate a graph
        this_team_ave_df = pd.DataFrame()
        this_team_ave_df['criterion'] = crit_list
        this_team_ave_df['self'] = crit_self_ave
        this_team_ave_df['shadow'] = crit_shadow_ave
        this_team_ave_df['tutor'] = crit_tutor_ave
        this_team_ave_df['client'] = crit_client_ave
        # report the team ave and the class ave
        this_team_ave_df['team_ave'] = this_team_ave_df.mean(axis=1)
        this_team_ave_df['class_ave'] = class_ave_list

        # now create the team chart
        this_team_ave_df.set_index("criterion",drop=True,inplace=True)
        print(this_team_ave_df)
        f.make_audit_chart(this_team_ave_df, c.d['charts'] + team + "_audit.png")
    
        # run the format audit feedback for anon/conf as defined below
        format_audit_feedback(team, 'conf')
        format_audit_feedback(team, 'anon')

        # compile the anon feedback for students
        files = [c.d['files'] + 'text_preamble.md', c.d['md'] + team + "_tmc_anon.md", c.d['md'] + team + "_audit_anon.md", c.d['files'] + 'text_changelog.md']
        with open(c.d['md'] + team + "_" + cfg['assignment']['assignment_short'] + "_audit_anon.md", 'w') as outfile:
            for fname in files:
                with open(fname) as infile:
                    outfile.write(infile.read())

        # compile the conf feedback for teaching team
        files = [c.d['md'] + team + "_tmc_conf.md", c.d['md'] + team + "_audit_conf.md"]
        with open(c.d['md'] + team + "_" + cfg['assignment']['assignment_short'] + "_audit_conf.md", 'w') as outfile:
            for fname in files:
                with open(fname) as infile:
                    outfile.write(infile.read())


        # convert md to pdf
        f.pandoc_html_toc(team + "_" + cfg['assignment']['assignment_short'] + "_audit_anon", team, 'anon')
        f.pandoc_html_toc(team + "_" + cfg['assignment']['assignment_short'] + "_audit_conf", team, 'conf')

        f.pandoc_pdf(team + "_" + cfg['assignment']['assignment_short'] + "_audit_anon")
        f.pandoc_pdf(team + "_" + cfg['assignment']['assignment_short'] + "_audit_conf")


# print feedback loop
def format_audit_feedback(team, kind):
    cfg=f.config_exists()

    # open and create a file for the yaml
    with open(c.d['yaml'] + team + '.yaml', 'w') as out:
        f.pandoc_yaml(out, team)

    # open and create a file for the css
    with open(c.d['css'] + team + "_" + kind + '.css', 'w') as out:
        f.pandoc_css(out, team, kind)

    with open(c.d["md"] + team + '_audit_' + kind + '.md', 'w') as out:

        # layout the audit chart
        this_chart=c.d['charts'] + team + "_audit.png"
        print("\n\n# " + cfg['audit_pdf']['audit_chart_header'] + "\n\n", file=out)
        print('![](../../.' + this_chart + ')\n\n', file=out)
        print( cfg['audit_pdf']['audit_chart_caption'] + "\n\n", file=out )
        
        # set up the dfs for all of the clients
        crit=f.filter_row('fields', 'field', 'crit_')
        comment=f.filter_row('fields', 'field', 'comment_')
        
        f.many_eyes_dataframe_sort('data_self')
        f.many_eyes_dataframe_sort('data_shadow')

        self_df=f.load_tsv('data_self_sorted')
        shadow_df=f.load_tsv('data_shadow_sorted')
        tutor_df=c.df['data_tutor']
        tutor_df.replace(cfg['audit_chart']['find_labels'], cfg['audit_chart']['replace_values'], inplace=True) 
        client_df=c.df['data_client']
        client_df.replace(cfg['audit_chart']['find_client_labels'], cfg['audit_chart']['replace_client_values'], inplace=True) 

        # filter this team's data
        this_team_self_df=self_df[self_df['team'].str.contains(team)].copy()
        this_team_shadow_df=shadow_df[shadow_df['team'].str.contains(team)].copy()
        this_team_tutor_df=tutor_df[tutor_df['team'].str.contains(team)].copy()
        this_team_client_df=client_df[client_df['team'].str.contains(team, na=False)].copy()

        # deal with NAs
        this_team_self_df.fillna('',inplace=True)
        this_team_shadow_df.fillna('',inplace=True)
        this_team_tutor_df.fillna('',inplace=True)
        this_team_client_df.fillna('',inplace=True)
        
        #loop through the crit columns
        for j, row in crit.iterrows():

            this_team_self_crit_df=this_team_self_df[this_team_self_df['crit_text'].str.contains(row['label'])]
            this_team_shadow_crit_df=this_team_shadow_df[this_team_shadow_df['crit_text'].str.contains(row['label'])]

            # loop through the comment columns
            f.print_comment_header('field', row, out)
            for k, c_row in this_team_self_crit_df.iterrows():
                this_text = str(c_row['crit_comment'])
                if kind == 'conf':
                    if ( str(c_row['crit_comment']) == ""):
                        # print messages if the comment is empty
                        print("**Self Review - " + c_row['user'] + " (" + c_row['username'] + ")" + "**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                    else:
                        print("**Self Review - " + c_row['user'] + " (" + c_row['username'] + ")" + "**\n\n" + this_text + "\n\n", file=out)
                else:
                    if ( str(c_row['crit_comment']) == ""):
                        print("**Self Review**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                    else:
                        print("**Self Review**\n\n" + this_text + "\n\n", file=out)

            for k, c_row in this_team_shadow_crit_df.iterrows():
                this_text = str(c_row['crit_comment'])
                if kind == 'conf':
                    if ( str(c_row['crit_comment']) == ""):
                        # print messages if the comment is empty
                        print("**Shadow Review - " + c_row['user'] + " (" + c_row['username'] + ")" + "**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                    else:
                        print("**Shadow Review - " + c_row['user'] + " (" + c_row['username'] + ")" + "**\n\n" + this_text + "\n\n", file=out)
                else:
                    if ( str(c_row['crit_comment']) == ""):
                        print("**Shadow Review**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                    else:
                        print("**Shadow Review**\n\n" + this_text + "\n\n", file=out)
        
        # print the anonymous comments
        for j, row in comment.iterrows():
            this_field=row['field']
            if this_field != 'comment_confidential':
                f.print_comment_header('field', row, out)
                for k, c_row in this_team_tutor_df.iterrows():
                    this_text = str(c_row[this_field])
                    print("**Tutor**\n\n" + this_text + "\n\n", file=out)
                for k, c_row in this_team_client_df.iterrows():
                    this_text = str(c_row[this_field])
                    print("**Client**\n\n" + this_text + "\n\n", file=out)

        # print the confidential comments
        if kind == 'conf':
            print("\n\n# Confidential feedback about the team progress", file=out)
            self_conf_df=c.df['data_self'].copy()
            this_team_self_conf_df=self_conf_df[self_df['team'].str.contains(team)]

            for j, row in this_team_self_conf_df.iterrows():            
                if ( str(row['comment_confidential']) == ""):
                    # print messages if the comment is empty
                    print("**" + row['user'] + " (" + row['username'] + ")" + "**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                else:
                    print("**" + row['user'] + " (" + row['username'] + ")" + "**\n\n" + str(row['comment_confidential']) + "\n\n", file=out)

# print message to console - complete!
f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
