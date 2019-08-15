#!/usr/bin/env python3
# python ./scripts/feedback_many_eyes.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the marks spreadsheet into pdf feedback'''

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
    data_self=f.load_tsv('data_self')
    data_shadow=f.load_tsv('data_shadow')
    data_tutor=f.load_tsv('data_tutor')
    data_client=f.load_tsv('data_client')

    # crit_levels=f.load_tsv('crit_levels')

    # # create a df of just the crit and the comments
    # crit=f.filter_row('fields', 'field', 'crit_')
    # comm=f.filter_row('fields', 'field', 'comment_')

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])
    
    # load data and create list of teams
    teams=f.load_tsv('students')
    teams.drop_duplicates(subset=['projectteam'], keep='first', inplace=True)
    team_list=[]

    crit_levels=f.load_tsv('crit_levels')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields', 'field', 'crit_')
    comment=f.filter_row('fields', 'field', 'comment_')
    crit_list=[]
    for j, row in crit.iterrows():
            crit_list.append(row['label'])

    self_df=c.df['data_self']
    self_df.replace(cfg['audit_chart']['find_labels'], cfg['audit_chart']['replace_values'], inplace=True) 
    self_a_df=self_df[['username', 'team', 'crit_a', 'crita_text', 'crita_comment']]
    self_b_df=self_df[['username', 'team', 'crit_b', 'critb_text', 'critb_comment']]
    self_a_df.rename(columns={'crit_a': 'crit_val'}, inplace=True)
    self_a_df.rename(columns={'crita_text': 'crit_text'}, inplace=True)
    self_a_df.rename(columns={'crita_comment': 'crit_comment'}, inplace=True)
    self_b_df.rename(columns={'crit_b': 'crit_val'}, inplace=True)
    self_b_df.rename(columns={'critb_text': 'crit_text'}, inplace=True)
    self_b_df.rename(columns={'critb_comment': 'crit_comment'}, inplace=True)
    self_frames = [self_a_df, self_b_df]
    self_df = pd.concat(self_frames, ignore_index=True, sort=False)

    shadow_df=c.df['data_shadow']
    shadow_df.replace(cfg['audit_chart']['find_labels'], cfg['audit_chart']['replace_values'], inplace=True) 
    shadow_a_df=shadow_df[['username', 'team', 'crit_a', 'crita_text', 'crita_comment']]
    shadow_b_df=shadow_df[['username', 'team', 'crit_b', 'critb_text', 'critb_comment']]
    shadow_a_df.rename(columns={'crit_a': 'crit_val'}, inplace=True)
    shadow_a_df.rename(columns={'crita_text': 'crit_text'}, inplace=True)
    shadow_a_df.rename(columns={'crita_comment': 'crit_comment'}, inplace=True)
    shadow_b_df.rename(columns={'crit_b': 'crit_val'}, inplace=True)
    shadow_b_df.rename(columns={'critb_text': 'crit_text'}, inplace=True)
    shadow_b_df.rename(columns={'critb_comment': 'crit_comment'}, inplace=True)
    shadow_frames = [shadow_a_df, shadow_b_df]
    shadow_df = pd.concat(shadow_frames, ignore_index=True, sort=False)


    tutor_df=c.df['data_tutor']
    tutor_df.replace(cfg['audit_chart']['find_labels'], cfg['audit_chart']['replace_values'], inplace=True) 

    client_df=c.df['data_client']
    client_df.replace(cfg['audit_chart']['find_client_labels'], cfg['audit_chart']['replace_client_values'], inplace=True) 

    class_self_ave=[]
    class_shadow_ave=[]
    class_tutor_ave=[]
    class_client_ave=[]
    
    #loop through the crit columns
    for j, row in crit.iterrows():
        # print(row['label'])
        class_self_crit_df=self_df[self_df['crit_text'].str.contains(row['label'])]
        class_shadow_crit_df=shadow_df[shadow_df['crit_text'].str.contains(row['label'])]
                
        class_self_ave.append(class_self_crit_df['crit_val'].mean())
        class_shadow_ave.append(class_shadow_crit_df['crit_val'].mean())
        class_tutor_ave.append(tutor_df[row['field']].mean())
        class_client_ave.append(client_df[row['field']].mean())

    class_ave_df = pd.DataFrame()
    class_ave_df['criterion'] = crit_list
    class_ave_df['self'] = class_self_ave
    class_ave_df['shadow'] = class_shadow_ave
    class_ave_df['tutor'] = class_tutor_ave
    class_ave_df['client'] = class_client_ave
    class_ave_df['class_ave'] = class_ave_df.mean(axis=1)

    class_ave_list = class_ave_df["class_ave"].values

    for i, row in teams.iterrows():
        this_team = row['projectteam']
        team_list.append(this_team)
    # for each team 
    for team in team_list: 
        print(team)
        this_team_self_df=self_df[self_df['team'].str.contains(team)]
        this_team_shadow_df=shadow_df[shadow_df['team'].str.contains(team)]
        this_team_tutor_df=tutor_df[tutor_df['team'].str.contains(team)]
        this_team_client_df=client_df[client_df['team'].str.contains(team, na=False)]

        crit_self_ave=[]
        crit_shadow_ave=[]
        crit_tutor_ave=[]
        crit_client_ave=[]

        this_out = team
        #open up a file to print to
        
    
        #loop through the crit columns
        for j, row in crit.iterrows():
            # print(row['label'])
            this_team_self_crit_df=this_team_self_df[this_team_self_df['crit_text'].str.contains(row['label'])]
            this_team_shadow_crit_df=this_team_shadow_df[this_team_shadow_df['crit_text'].str.contains(row['label'])]
            #print(this_team_crit_df)
            crit_self_ave.append(this_team_self_crit_df['crit_val'].mean())
            crit_shadow_ave.append(this_team_shadow_crit_df['crit_val'].mean())
            crit_tutor_ave.append(this_team_tutor_df[row['field']].mean())

            with open(c.d["md"] + this_out + '_audit.md', 'w') as out:

                # print graph
                this_chart=c.d['charts'] + team + "_audit.png"

                print("\n\n# " + cfg['audit_pdf']['audit_chart_header'] + "\n\n", file=out)
                
                print('![](../../.' + this_chart + ')\n\n', file=out)
                print( cfg['audit_pdf']['audit_chart_caption'] + "\n\n", file=out )
        

                for j, row in crit.iterrows():
                # loop through the comment columns
                    f.print_comment_header('field', row, out)
                    for k, c_row in this_team_self_crit_df.iterrows():
                        this_text = str(c_row['crit_comment'])
                        print("**Self Review**\n\n" + this_text + "\n\n", file=out)
                    for k, c_row in this_team_shadow_crit_df.iterrows():
                        this_text = str(c_row['crit_comment'])
                        print("**Shadow Review**\n\n" + this_text + "\n\n", file=out)
        
                for j, row in comment.iterrows():
                    this_field=row['field']
                    if this_field != 'comment_c':
                        f.print_comment_header('field', row, out)
                        for k, c_row in this_team_tutor_df.iterrows():
                            this_text = str(c_row[this_field])
                            print("**Tutor**\n\n" + this_text + "\n\n", file=out)
                        for k, c_row in this_team_client_df.iterrows():
                            this_text = str(c_row[this_field])
                            print("**Client**\n\n" + this_text + "\n\n", file=out)
                
        if this_team_client_df.empty:
            for l, row in crit.iterrows():
                crit_client_ave.append('0')
        else:
            for l, row in crit.iterrows():
                crit_client_ave.append(this_team_client_df[row['field']].mean())

        this_team_ave_df = pd.DataFrame()
        this_team_ave_df['criterion'] = crit_list
        this_team_ave_df['self'] = crit_self_ave
        this_team_ave_df['shadow'] = crit_shadow_ave
        this_team_ave_df['tutor'] = crit_tutor_ave
        this_team_ave_df['client'] = crit_client_ave

        this_team_ave_df['team_ave'] = this_team_ave_df.mean(axis=1)
        this_team_ave_df['class_ave'] = class_ave_list

        this_team_ave_df.set_index("criterion",drop=True,inplace=True)

        f.make_audit_chart(this_team_ave_df, c.d['charts'] + team + "_audit.png")

        this_chart=c.d['charts'] + team + ".png"

        # define the out files
        # note that the pdf will be copied as out in wattle_csv.py
                      
        with open(c.d["yaml"] + this_out + '.yaml', 'w') as out:
        # create the pandoc header
            f.pandoc_yaml(out, team)

        with open(c.d["css"] + this_out + '.css', 'w') as out:
        # create the pandoc header
            f.pandoc_css(out, team)

        files = [c.d['files'] + 'text_preamble.md', c.d['md'] + this_out + "_tmc_anon.md", c.d['md'] + this_out + "_audit.md", c.d['files'] + 'text_changelog.md']
        with open(c.d['md'] + this_out + ".md", 'w') as outfile:
            for fname in files:
                with open(fname) as infile:
                    outfile.write(infile.read())

        # convert md to pdf using the shell
        f.pandoc_pdf(this_out, '2')

 
    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
