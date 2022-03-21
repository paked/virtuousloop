#!/usr/bin/env python3
# python ./scripts/analysis_many_eyes.py
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
import readability
from bs4 import BeautifulSoup as soup
from wordcloud import WordCloud
import subprocess
import matplotlib.pyplot as plt
import json
import hashlib


def analysis_many_eyes():

    cfg = f.load_config()

    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])

    # load in tsvs of needed fields
    student = f.load_tsv('students')
    student.drop_duplicates(keep='first', inplace=True)
    student.dropna(how='any', subset=['user'], inplace=True)
    students = student.copy()

    fields = f.load_tsv('fields')
    crit_levels = f.load_tsv('crit_levels')

    data_self = f.load_tsv('data_self')
    data_shadow = f.load_tsv('data_shadow')
    data_tutor = f.load_tsv('data_tutor')
    data_client = f.load_tsv('data_client')

    # create a df of just the crit and the comments
    crit = f.filter_row('fields', 'field', 'crit_')
    comm = f.filter_row('fields', 'field', 'comment_')

    # print message to console
    f.pnt_info(c.msg["console_reading_feedback_files"])
    
    # load data and create list of teams
    teams = f.load_tsv('students')
    teams.drop_duplicates(subset=['group'], keep='first', inplace=True)

    # create a team list to iterate through
    team_list = []
    for i, row in teams.iterrows():
        this_team = row['group']
        team_list.append(this_team)

    # create a list of crit for access
    crit_list = []
    crit_list_header = ['team','role']
    for j, row in crit.iterrows():
         crit_list.append(row['label'])
         crit_list_header.append(row['label'])

    # create a list of comments for access
    comment_list=f.create_list(comm, 'field')

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

    f.pnt_info(c.msg["console_many_eyes"])

    print("Cleaning the self data...")
    for i, row in self_df.iterrows():
        for readability_list in cfg['analytics']['readability_stats']:
            f.readability_stats('data_self_sorted', row, i, 'crit_comment', readability_list[0], readability_list[1], readability_list[2])

    print("Cleaning the shadow data...")
    for i, row in shadow_df.iterrows():
        for readability_list in cfg['analytics']['readability_stats']:
            f.readability_stats('data_shadow_sorted', row, i, 'crit_comment', readability_list[0], readability_list[1], readability_list[2])

    team_stats_list=[]

    # report to the console
    print('Generating team stats...')

    # for each team 
    for team in team_list: 
        # work through the many eyes data
        for eye in cfg['many_eyes']['eyes']:
            this_stats_list = [team, eye]
            this_df=locals()[eye + "_df"]
            this_crit_df=this_df[this_df['team'].str.contains(team, na=False)]

            if not this_crit_df.empty:
                for j, row in crit.iterrows():

                    if eye == 'self' or eye == 'shadow':
                        this_crit_df=this_df[this_df['crit_text'].str.contains(row['label'])]
                        this_stats_list.append(this_crit_df['crit_val'].mean())
                    else:
                        try:
                            this_stats_list.append(this_crit_df[row['field']].mean())
                        except:
                            this_stats_list.append(0)
            
            team_stats_list.append(this_stats_list)

    team_stats = pd.DataFrame(team_stats_list, columns = crit_list_header)
    team_stats_ave_list=[]
    for team in team_list: 

        this_team_stats = team_stats[team_stats['team'].str.contains(team)]

        this_team_ave_list=[team, 'average']
        for crit in crit_list:
            this_team_crit_mean=this_team_stats[crit].mean()
            this_team_ave_list.append(this_team_crit_mean)
        
        team_stats_ave_list.append(this_team_ave_list)

    team_stats_ave_df = pd.DataFrame(team_stats_ave_list, columns = crit_list_header)

    frames = [team_stats, team_stats_ave_df]
    team_stats_df = pd.concat(frames)

    crit=f.filter_row('fields', 'field', 'crit_')

    # report to the console
    print('Generating team charts...')
    for team in team_list: 
        print(team)        
        #loop through the crit columns
        for i, row in crit.iterrows():
            this_crit_label=row['label']
            this_crit_field=row['field']

            this_team_crit_list=[]
            this_team_crit_header=['role', 'value']
            for eye in cfg['many_eyes']['eyes']:
                this_df=locals()[eye + "_df"]
                this_team_df=this_df[this_df['team'].str.contains(team, na=False)]
                if not this_team_df.empty:
                    if eye == 'self' or eye == 'shadow':
                        this_team_crit_df=this_team_df[this_team_df['crit_text'].str.contains(this_crit_label)]
                        for j, row in this_team_crit_df.iterrows():
                            this_team_crit_list.append([eye, row['crit_val']])
                    else:
                        for j, row in this_team_df.iterrows():
                            try:
                                this_team_crit_list.append([eye, row[this_crit_field]])
                            except:
                                this_team_crit_list.append([eye, 0])
            this_team_crit_df = pd.DataFrame(this_team_crit_list, columns = this_team_crit_header).T
            this_team_crit_df.columns = this_team_crit_df.iloc[0]
            this_team_crit_df = this_team_crit_df.iloc[1:].rename_axis(None, axis=1)
            this_team_crit_df['average']=this_team_crit_df.mean(axis=1)
            f.make_audit_crit_chart(this_team_crit_df, c.d['charts'] + team + "_" + this_crit_field + "_audit.png")
    
    
    self_crit_val_diff_list = []
    self_crit_val_abs_list = []
    self_wps_list = []
    for i, row in self_df.iterrows():
        this_crit_val = row['crit_val']
        this_crit_text = row['crit_text']
        this_team = row['team']
        this_wc = row['wc']
        this_sc = row['sc']

        this_team_row = team_stats_ave_df[team_stats_ave_df['team'].str.contains(this_team)]
        # this_crit_ave = this_team_row.iloc[0][this_crit_text]
        this_crit_ave = 0
        
        this_diff = this_crit_val - this_crit_ave
        this_diff_abs = abs(this_diff)
        
        self_crit_val_diff_list.append(this_diff)
        self_crit_val_abs_list.append(this_diff_abs)

        this_wps = this_wc / this_sc
        self_wps_list.append(this_wps)

    self_df['crit_val_diff'] = self_crit_val_diff_list
    self_df['crit_val_abs'] = self_crit_val_abs_list
    self_df['wps'] = self_wps_list

    shadow_crit_val_diff_list = []
    shadow_crit_val_abs_list = []
    shadow_wps_list = []
    for i, row in shadow_df.iterrows():
        print(shadow_df)
        this_crit_val=row['crit_val']
        this_crit_text=row['crit_text']
        this_team=row['team']
        this_wc=row['wc']
        this_sc=row['sc']

        this_team_row=team_stats_ave_df[team_stats_ave_df['team'].str.contains(this_team)]
        if not this_team_row.empty:
            this_crit_ave=this_team_row.iloc[0][this_crit_text]
        else:
            this_crit_ave=0

        this_diff=this_crit_val - this_crit_ave
        this_diff_abs=abs(this_diff)

        shadow_crit_val_diff_list.append(this_diff)
        shadow_crit_val_abs_list.append(this_diff_abs)

        this_wps=this_wc / this_sc
        shadow_wps_list.append(this_wps)

    shadow_df['crit_val_diff']=shadow_crit_val_diff_list
    shadow_df['crit_val_abs']=shadow_crit_val_abs_list
    shadow_df['wps']=shadow_wps_list

    self_df['wc_pct_rank']=self_df.wc.rank(pct=True)
    self_df['wps_pct_rank']=self_df.sc.rank(pct=True)
    self_df['flesch_pct_rank']=self_df.flesch.rank(pct=True)
    self_df['crit_val_diff_rank']=self_df.crit_val_diff.rank(pct=True)

    shadow_df['wc_pct_rank']=shadow_df.wc.rank(pct=True)
    shadow_df['wps_pct_rank']=shadow_df.sc.rank(pct=True)
    shadow_df['flesch_pct_rank']=shadow_df.flesch.rank(pct=True)
    shadow_df['crit_val_diff_rank']=shadow_df.crit_val_diff.rank(pct=True)

    wc_score=[-2, -1, 0, 1, 2]
    wps_score=[-2, -1, 0, 1, 2]
    flesch_score=[2, 1, 0, -1, -2]
    cvd_score=[2, 1, 0, -1, -2]
    wc_score_actual=[-2, -1, 0, 1, 2]

    score_pct=[0.2, 0.4, 0.6, 0.8, 1.0]
    score_act=[25, 50, 100, 200, 10000]

    
    score_dataframe(self_df, 'wc_pct_rank', 'wc_score', wc_score, score_pct)
    score_dataframe(shadow_df, 'wc_pct_rank', 'wc_score', wc_score, score_pct)
    score_dataframe(self_df, 'wps_pct_rank', 'wps_score', wps_score, score_pct)
    score_dataframe(shadow_df, 'wps_pct_rank', 'wps_score', wps_score, score_pct)
    score_dataframe(self_df, 'flesch_pct_rank', 'flesch_score', flesch_score, score_pct)
    score_dataframe(shadow_df, 'flesch_pct_rank', 'flesch_score', flesch_score, score_pct)
    score_dataframe(self_df, 'crit_val_diff_rank', 'crit_val_score', cvd_score, score_pct)
    score_dataframe(shadow_df, 'crit_val_diff_rank', 'crit_val_score', cvd_score, score_pct)
    
    score_dataframe(self_df, 'wc', 'wc_score_act', wc_score, score_act)    
    score_dataframe(shadow_df, 'wc', 'wc_score_act', wc_score, score_act)

    col_chart_list=["wc", "wps", "flesch", "crit_val_diff"]

    for col in col_chart_list:

        if col == "flesch":
            chart_min=0
            chart_max=100
        elif col == "crit_val_diff":
            chart_min=-5
            chart_max=5
        else:
            chart_min=0
            self_max=self_df[col].max()
            shadow_max=shadow_df[col].max()
            if self_max > shadow_max:
                this_max=self_max
            else:
                this_max=shadow_max
            chart_max=int(round(this_max/20))*20


        f.make_col_chart(self_df, col, 'self', chart_min, chart_max)
        f.make_col_chart(shadow_df, col, 'shadow', chart_min, chart_max)

    # for each team 
    for i, row in students.iterrows():
        # report to the console
        this_user=str(row['user'])
        this_first=str(row['firstname'])
        this_last=str(row['lastname'])
        self_team=str(row['group'])
        shadow_team=str(row['shadowteam'])

        print(this_user)

        this_self_df=self_df[self_df['username'].str.contains(this_user)]
        this_shadow_df=shadow_df[shadow_df['username'].str.contains(this_user)]

        if this_self_df.empty and this_shadow_df.empty:
            with open(c.d["md"] + str(this_user) + '.md', 'w') as out:
                print("## " + this_user + " - " + this_first + " " + this_last + "\n\n", file=out)
                print("**No reviews received.**\n\n", file=out)
        else:
            try:

                local_text_analysis(this_self_df, this_user, 'self')
                local_text_analysis(this_shadow_df, this_user, 'shadow')

                with open(c.d["md"] + str(this_user) + '.md', 'w') as out:
                    print("## " + this_user + " - " + this_first + " " + this_last + "\n\n", file=out)
                    print("**This feedback report shows analytics on the feedback you gave in the review.**\n\n", file=out)
                    print("By considering the analytics in this report, you should get a sense of how your feedback compares to others. This is provided for information to help guide expectations around feedback.\n\n", file=out)
                    print("# Project Audits\n\n", file=out)
                    print("*Compare your review to others' perspectives.*\n\n", file=out)
                    print("It is expected that there will be some differences between reviews. You should consider your review compared to others and whether the discrepancy is due to a difference of opinion or if you have not seen the whole picture when undertaking your review. Use these data as a prompt for discussion within your team and with your shadows.\n\n", file=out)
                    print("## Project Team: " + self_team + "\n\n", file=out)
                    if this_self_df.empty:
                        print("* No review submitted", file=out)
                    else:
                        for i, row in this_self_df.iterrows():

                            print("*Your review of " + str(row['crit_text']) + ":* **" + str(row['crit_desc']) + "**\n\n", file=out)
                            this_crit=f.filter_row('fields', 'label', row['crit_text'])
                            for j, j_row in this_crit.iterrows():
                                this_crit_field=j_row['field']
                                print("![](../../." + c.d['charts']+ self_team + "_" + this_crit_field + "_audit.png)\n\n", file=out)
                            print("\n*Chart of all reviews of " + self_team + " for " + str(row['crit_text']) + "*\n\n", file=out)

                    print("<div class=\"new-page\">.</div>", file=out)
                    print("## Shadow Team: " + shadow_team + "\n\n", file=out)
                    if this_shadow_df.empty:
                        print("* No review submitted", file=out)
                    else:
                        for i, row in this_shadow_df.iterrows():
                            print("*Your review of " + str(row['crit_text']) + ":* **" + str(row['crit_desc']) + "**\n\n", file=out)
                            this_crit=f.filter_row('fields', 'label', row['crit_text'])
                            for j, j_row in this_crit.iterrows():
                                this_crit_field=j_row['field']
                                print("![](../../." + c.d['charts'] + shadow_team + "_" + this_crit_field + "_audit.png)\n\n", file=out)
                            print("\n*Chart of all reviews of " + shadow_team + " for " + str(row['crit_text']) + "*\n\n", file=out)

                    print("<div class=\"new-page\">.</div>", file=out)
                    print("## Difference in review evaluations\n\n", file=out)
                    print("The difference in review evaluations helps to compare how your reviews compare to the average reviews from the 'many eyes'.\n\n", file=out)
                    print("A negative value likely indicates that your review was below the average of reviews (i.e. on the more pessimistic side of the reviewers)."
                          " A positive value likely indicates that your review was above the average of reviews (i.e. on the more optimistic side of the reviewers)."
                          " '1' represents a 'half band', such as the difference between 'Baseline' and 'Baseline-Acceptable'. '2' represents a 'full band', such as the difference between 'Baseline' and 'Acceptable'."
                          " It is common to see the Self Reviews as more positive than the Shadow Reviews. "
                          " This could be a prompt for a discussion between the Team and Shadows to help reconcile opinions and develop better understanding of each other's work*\n\n", file=out)

                    this_head=["Team","Role"]
                    this_self_list=[self_team,"Self"]
                    this_shadow_list=[shadow_team,"Shadow"]

                    if not this_self_df.empty:
                        for i, row in this_self_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_self_list.append("**" + str(int(round(row['crit_val_diff']*4)/4)) + "** half-bands")
                            except:
                                this_self_list.append("**N/A**")
                    this_head.append("Class Average")
                    try:
                        this_self_list.append(str(int(round(self_df['crit_val_abs'].mean()*4)/4)) + " (self)")
                    except:
                        this_self_list.append("**N/A**")

                    if not this_shadow_df.empty:
                        for i, row in this_shadow_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_shadow_list.append("**" + str(int(round(row['crit_val_abs']*4)/4)) + "** half-bands")
                            except:
                                this_self_list.append("**N/A**")

                    this_head.append("Class Average")
                    try:
                        this_shadow_list.append(str(int(round(shadow_df['crit_val_abs'].mean()*4)/4))  + " (shadow)")
                    except:
                        this_shadow_list.append("**N/A**")

                    this_html_df=pd.DataFrame(list(zip(this_head, this_self_list, this_shadow_list))).T
                    this_html_df.columns = this_html_df.iloc[0]
                    this_html_df = this_html_df.iloc[1:].rename_axis(None, axis=1)
                    # this_html_df.set_index("Team",drop=True,inplace=True)
                    print(this_html_df.to_html(), file=out)

                    print("![](../../." + c.d['charts'] + "crit_val_diff_self.png)\n", file=out)
                    print("![](../../." + c.d['charts'] + "crit_val_diff_shadow.png)\n", file=out)
                    print("\n*Top: Histogram of differences for self reviews.*", file=out)
                    print("*Bottom: Histogram of differences for shadow reviews.*\n\n", file=out)
                    print("<div class=\"new-page\">.</div>", file=out)


                    print("# Descriptive statistics about your comments\n\n", file=out)
                    print("## Word Count\n\n", file=out)
                    print("The course guide requests you to complete 250-500 words per review.\n\n", file=out)
                    print("These data are provided for information to help benchmark the quantity of feedback you are providing in the reviews."
                          " Note that 'more' is not necessarily better, but 'enough' is needed to provide value in the process."
                          " Locate on the histograms where your feedback is situated: if it falls on the lower end, then consider providing more feedback in the next audit; if it falls on the upper end, then you have likely been helpful in the audit.\n\n", file=out)

                    print("*Table of your review word count statistics*\n\n", file=out)

                    this_head=["Team","Role"]
                    this_self_list=[self_team,"Self"]
                    this_shadow_list=[shadow_team,"Shadow"]

                    if not this_self_df.empty:
                        for i, row in this_self_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_self_list.append("**" + str(int(round(row['wc']))) + "** words")
                            except:
                                this_self_list.append("**N/A**")

                    this_head.append("Class Average")
                    try:
                        this_self_list.append(str(int(round(self_df['wc'].mean()))) + " (self)")
                    except:
                        this_self_list.append("**N/A**")

                    if not this_shadow_df.empty:
                        for i, row in this_shadow_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_shadow_list.append("**" + str(int(round(row['wc']))) + "** words")
                            except:
                                this_shadow_list.append("**N/A**")

                    this_head.append("Class Average")
                    try:
                        this_shadow_list.append(str(int(round(shadow_df['wc'].mean())))  + " (shadow)")
                    except:
                        this_shadow_list.append("**N/A**")
                    this_html_df=pd.DataFrame(list(zip(this_head, this_self_list, this_shadow_list))).T
                    this_html_df.columns = this_html_df.iloc[0]
                    this_html_df = this_html_df.iloc[1:].rename_axis(None, axis=1)
                    # this_html_df.set_index("Team",drop=True,inplace=True)
                    print(this_html_df.to_html(), file=out)

                    print("![](../../." + c.d['charts'] + "wc_self.png)\n", file=out)
                    print("![](../../." + c.d['charts'] + "wc_shadow.png)\n", file=out)
                    print("\n*Top: Histogram of word counts for self reviews.*", file=out)
                    print("*Bottom: Histogram of word counts for shadow reviews.*\n\n", file=out)
                    print("<div class=\"new-page\">.</div>", file=out)
                    print("## Words per Sentence Count\n\n", file=out)
                    print("Generally, shorter sentences are easier to read.\n\n", file=out)
                    print("This is a descriptive statistic that might prompt you to consider how to write clearer feedback. "
                          " If you find yourself at the higher end of the histogram, consider putting your feedback together in shorter sentences to help readability"
                          " If you find yourself as an outlier at the lower end of the histogram, consider how to put together your feedback in fuller sentences.\n\n", file=out)
                    print("*Table of your review words per sentence count statistics*\n\n", file=out)

                    this_head=["Team","Role"]
                    this_self_list=[self_team,"Self"]
                    this_shadow_list=[shadow_team,"Shadow"]

                    if not this_self_df.empty:
                        for i, row in this_self_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_self_list.append("**" + str(int(round(row['wps']))) + "** wps")
                            except:
                                this_self_list.append("**N/A**")

                    this_head.append("Class Average")
                    try:
                        this_self_list.append(str(int(round(self_df['wps'].mean()))) + " (self)")
                    except:
                        this_self_list.append("**N/A**")

                    if not this_shadow_df.empty:
                        for i, row in this_shadow_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_shadow_list.append("**" + str(int(round(row['wps']))) + "** wps")
                            except:
                                this_shadow_list.append("**N/A**")

                    this_head.append("Class Average")
                    try:
                        this_shadow_list.append(str(int(round(shadow_df['wps'].mean())))  + " (shadow)")
                    except:
                        this_shadow_list.append("**N/A**")

                    this_html_df=pd.DataFrame(list(zip(this_head, this_self_list, this_shadow_list))).T
                    this_html_df.columns = this_html_df.iloc[0]
                    this_html_df = this_html_df.iloc[1:].rename_axis(None, axis=1)
                    # this_html_df.set_index("Team",drop=True,inplace=True)
                    print(this_html_df.to_html(), file=out)

                    print("![](../../." + c.d['charts'] + "wps_self.png)\n", file=out)
                    print("![](../../." + c.d['charts'] + "wps_shadow.png)\n", file=out)
                    print("\n*Top: Histogram of sentence counts for self reviews.*", file=out)
                    print("*Bottom: Histogram of sentence counts for shadow reviews.*\n\n", file=out)
                    
                    print("<div class=\"new-page\">.</div>", file=out)
                    print("## Flesch–Kincaid readability test\n\n", file=out)
                    print("Based on a score out of 100, lower scores are typically harder to read: scores below 50 are considered difficult to read. [More information on Wikipedia](https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests)\n\n", file=out)
                    print(" All readability tests are problematic and have limitations. If you would like to improve your readability score, consider reducing the number of words per sentence (i.e. shorter sentences) or reducing the number of syllables per word (i.e. shorter words).\n\n", file=out)
                    print("*Table of your Flesch–Kincaid readability score statistics*\n\n", file=out)

                    this_head=["Team","Role"]
                    this_self_list=[self_team,"Self"]
                    this_shadow_list=[shadow_team,"Shadow"]

                    if not this_self_df.empty:
                        for i, row in this_self_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_self_list.append("**" + str(int(round(row['flesch']))) + "**")
                            except:
                                this_self_list.append("**N/A**")
                    
                    this_head.append("Class Average")
                    try:
                        this_self_list.append(str(int(round(self_df['flesch'].mean()))) + " (self)")
                    except:
                        this_self_list.append("**N/A**")

                    if not this_shadow_df.empty:
                        for i, row in this_shadow_df.iterrows():
                            try:
                                this_head.append(str(row['crit_text']))
                                this_shadow_list.append("**" + str(int(round(row['flesch']))) + "**")
                            except:
                                this_shadow_list.append("**N/A**")
                    
                    this_head.append("Class Average")
                    try:
                        this_shadow_list.append(str(int(round(shadow_df['flesch'].mean())))  + " (shadow)")
                    except:
                        this_shadow_list.append("**N/A**")

                    this_html_df=pd.DataFrame(list(zip(this_head, this_self_list, this_shadow_list))).T
                    this_html_df.columns = this_html_df.iloc[0]
                    this_html_df = this_html_df.iloc[1:].rename_axis(None, axis=1)
                    # this_html_df.set_index("Team",drop=True,inplace=True)
                    print(this_html_df.to_html(), file=out)

                    print("![](../../." + c.d['charts'] + "flesch_self.png)\n", file=out)
                    print("![](../../." + c.d['charts'] + "flesch_shadow.png)\n", file=out)
                    print("\n*Top: Histogram of Flesch-Kincaid readability for self reviews.*", file=out)
                    print("*Bottom: Histogram of Flesch-Kincaid readability for shadow reviews.*\n\n", file=out)

                    role_list=["self", "shadow"]

                    print("# Analytics generated from your comments", file=out)
                    print("\n*" + cfg['analytics']['nlp_source_comment']+  "*\n\n", file=out)
                    print("These data are views on your reviews using a natural language (NLP) API. NLP can be imprecise and produce some strange results; however, it does give a view of how your feedback is interpreted by a machine, and may provide some insights into where you might wish to place emphasise in your feedback.\n\n", file=out)

                    # using enumerate to access list indices for name and title
                    # work through the defined nlp endpoints
                    for num, endpoint in enumerate(cfg['aylien']['endpoints'], start=0):
                        name=(cfg['aylien']['endpoint_name'][num])
                        title=(cfg['aylien']['endpoint_title'][num])
                        
                        print("<article id=\"columns\">", file=out)
                        print("\n## Comment " + title + "\n\n", file=out)
                        if endpoint == "sentiment":
                            print("<section>", file=out)

                        # loop through the analysis for each comment
                        for role in role_list:

                            # load the nlp json response to read from
                            with open(c.d['nlp'] + this_user + "_comment_" + role + ".json") as json_file:
                                this_nlp = json.load(json_file)

                                # print a header to out
                                print("\n**" + title + " for " + role + " comments**" "\n\n", file=out)
                                if endpoint == "sentiment":
                                    item_out = ""
                                    for item in this_nlp[name]:
                                        item_out += item
                                    print("* " + item_out, file=out)
                                else:
                                    try: 
                                        item_check=[]
                                        item_out = ""
                                        for item in this_nlp[name]:
                                            # replace hashes so that they are not interpreted in markdown
                                            if endpoint != 'entities':
                                                item_out = item.replace("#", "\\#")
                                                print("* " + item_out, file=out)
                                            else:
                                                this_item=item.split(' ')
                                                item_out = this_item[0].replace("#", "\\#")
                                                if item_out not in item_check :
                                                    # print to out each item in a list
                                                    print("* " + item_out, file=out)
                                                    item_check.append(item_out)
                                    except:
                                        # if there's nothing there, print N/A
                                        print("* N/A", file=out)
                        
                        if endpoint == "sentiment":
                            print("</section>", file=out)
                        print("</article>", file=out)
                    print("\n\n# Wordclouds generated from your comments\n", file=out)

                    print("Wordclouds provide a simple visual representation of the frequency of words used in your feedback - words that appear larger were used more frequently. Wordclouds provide an indication of frequency; however are limited in providing context as to how the words are correlated or used in combination.\n\n",file=out)

                    # loop through the analysis for each comment
                    for role in role_list:
                        print("**Your " + role + " review**\n\n", file=out)
                        print("![](../../." + c.d['wordcloud'] + this_user + "_" + role + ".png)\n", file=out)
                        print("\n*Above: Wordcloud generated from feedback you gave in " + role + " reviews.*\n", file=out)
                        

                    print("\n\n# Record of submissions", file=out)

                    print("*Below is a record of your review submissions.* These should be as per your submission via Wattle, but may have formatting differences. If no submission was recorded, the record will state 'No Comment'.\n\n", file=out)

                    if this_self_df.empty:
                        print("* No review submitted", file=out)
                    else:
                        for i, row in this_self_df.iterrows():

                            print("**Your review of " + str(row['crit_text']) + " for " + self_team + "**\n\n", file=out)
                            print(str(row['crit_comment']) + "\n\n", file=out)

                    if this_shadow_df.empty:
                        print("* No review submitted", file=out)
                    else:
                        for i, row in this_shadow_df.iterrows():

                            print("**Your review of " + str(row['crit_text']) + " for " + shadow_team + "**\n\n", file=out)
                            print(str(row['crit_comment']) + "\n\n", file=out)
            except:
                with open(c.d["md"] + str(this_user) + '.md', 'w') as out:
                    print("## " + this_user + " - " + this_first + " " + this_last + "\n\n", file=out)
                    print("**Error in review compilation.**\n\n", file=out)


        # create the weasyprint variables
        with open(c.d['yaml'] + str(this_user) + '.yaml', 'w') as out:
            f.pandoc_yaml(out, str(this_user))
            
        # create the weasyprint stylesheet
        with open(c.d['css'] + str(this_user) + ".css", 'w') as out:
            f.pandoc_css(out, str(this_user), 'anon')

        # turn the pandoc md to html to pdf

        f.pandoc_html_single(str(this_user))
        f.pandoc_pdf(str(this_user))
    # loop through each row and create a secret for each student

    for i, row in students.iterrows():
        this_user = row['user']
        secret = hashlib.sha1(row['user'].encode('utf-8')).hexdigest()
        secret_file = this_user + "-" + secret + ".pdf"
        comment = "<a href=\"" + cfg['assignment']['feedback_url'] + "reviews/" + this_user + "-" + secret + ".pdf\">PDF Feedback on your Reviews</a>"
        
        # update the df
        students.loc[i,'secret'] = comment

        # cp pdf to secret here
        file_from = c.d['pdf'] + this_user + ".pdf"
        file_to = c.d['review'] + secret_file
        copyfile(file_from, file_to)

        this_self_df=self_df[self_df['username'].str.contains(this_user)]
        this_shadow_df=shadow_df[shadow_df['username'].str.contains(this_user)]

        self_wc_score=this_self_df['wc_score'].sum()
        shadow_wc_score=this_shadow_df['wc_score'].sum()
        self_wps_score=this_self_df['wps_score'].sum()
        shadow_wps_score=this_shadow_df['wps_score'].sum()
        self_flesch_score=this_self_df['flesch_score'].sum()
        shadow_flesch_score=this_shadow_df['flesch_score'].sum()

        self_crit_score=this_self_df['crit_val_score'].sum()
        shadow_crit_score=this_shadow_df['crit_val_score'].sum()

        this_text_score=self_wc_score + shadow_wc_score + self_wps_score + shadow_wps_score + self_flesch_score + shadow_flesch_score
        this_crit_score=self_crit_score + shadow_crit_score
        students.loc[i,'text_score'] = this_text_score
        students.loc[i,'crit_score'] = this_crit_score

    
    students['text_rank']=students.text_score.rank(pct=True)
    students['crit_rank']=students.crit_score.rank(pct=True)

    for i, row in students.iterrows():
        this_text_rank=row['text_rank']
        this_crit_rank=row['crit_rank']
        this_combined_rank=this_text_rank + this_crit_rank

        students.loc[i,'combined_rank'] = this_combined_rank

    students['score_rank']=students.combined_rank.rank(pct=True)


    this_out=students[['user','secret','text_score', 'crit_score', 'score_rank']]
    this_out.to_csv(c.f['wattle_analysis'], index=False)


# print message to console - complete!
f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))

def local_text_analysis(dataframe, user, role):

    if not dataframe.empty:
        # get the comment to pass to the nlp
        this_comment = " ".join(f.create_list(dataframe, "crit_comment"))

        # store the comment so that it can be accessed for the word cloud
        with open(c.d['txt'] + user + "_" + role + ".txt", 'w') as out:
            print(this_comment, file=out)

        # create a wordcloud using the wordcloud_cli interface

        if role == 'self':
            this_color = "RoyalBlue"
        else:
            this_color = "DarkGreen"

        subprocess.call("wordcloud_cli --width 1000 --height 250 --text " + c.d['txt'] + user + "_" + role + ".txt --imagefile " + c.d['wordcloud'] + user + "_" + role + ".png --fontfile ./includes/fonts/Roboto-Medium.ttf --background white --color " + this_color, shell=True)

        this_nlp_file = Path(c.d['nlp'] + user + "_comment_" + role + ".json")
        # check if the nlp data already exists
        # this is important only to reduce the numbers of calls on the api for local testing
        if not this_nlp_file.is_file():
            # get the results from the api
            this_nlp=f.text_analysis_api(this_comment, "comment_" + role, user)
            with open(this_nlp_file, 'w') as out:
                print(this_nlp, file=out)

def score_dataframe(dataframe, curr_col, score_col, score_list, score_vals):
    for i, i_row in dataframe.iterrows():
        # for score in wc_score:
        if i_row[curr_col] < score_vals[0]:
            dataframe.loc[i,score_col] = score_list[0]
        elif i_row[curr_col] < score_vals[1]:
            dataframe.loc[i,score_col] = score_list[1]
        elif i_row[curr_col] < score_vals[2]:
            dataframe.loc[i,score_col] = score_list[2]
        elif i_row[curr_col] < score_vals[3]:
            dataframe.loc[i,score_col] = score_list[3]
        elif i_row[curr_col] <= score_vals[4]:
            dataframe.loc[i,score_col] = score_list[4]