#!/usr/bin/env python3
# python ./scripts/analysis_marks.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''runs some basic analysis on the marks for moderation'''


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
import readability
from bs4 import BeautifulSoup as soup


def analysis_marks():
    
    # check that config exists
    cfg=f.config_exists()
    
    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])
    
    # load in tsvs of needed fields
    #fields=f.load_tsv('fields')
    f.load_tsv('marks')
    #crit_levels=f.load_tsv('crit_levels')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields', 'field', 'crit_')
    comm=f.filter_row('fields', 'field', 'comment_')

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])
    
    # create distribution charts for later
    stats=f.make_crit_list(crit)
    f.make_crit_chart(crit, stats)

    c.df['marks'].loc[c.df['marks'].grade_calculated == 0, ['marker_name', 'marker_id']] = 'No Submission', 'nil'

    

    for i, row in c.df['marks'].iterrows():
        f.html_to_text('marks', row, i, 'comment_a', 'comment_a_txt')
        f.html_to_text('marks', row, i, 'comment_b', 'comment_b_txt')
        
    for i, row in c.df['marks'].iterrows():
        f.readability_stats('marks', row, i, 'comment_a_txt', 'comment_a_wc', 'sentence info', 'words')
        f.readability_stats('marks', row, i, 'comment_b_txt', 'comment_b_wc', 'sentence info', 'words')
        f.readability_stats('marks', row, i, 'comment_a_txt', 'comment_a_sc', 'sentence info', 'sentences')
        f.readability_stats('marks', row, i, 'comment_b_txt', 'comment_b_sc', 'sentence info', 'sentences')

        f.readability_stats('marks', row, i, 'comment_a_txt', 'flesch_a', 'readability grades', 'FleschReadingEase')
        f.readability_stats('marks', row, i, 'comment_b_txt', 'flesch_b', 'readability grades', 'FleschReadingEase')

        f.text_analysis_api(row['comment_a_txt'], 'comment_a', row['user'])
        f.text_analysis_api(row['comment_b_txt'], 'comment_b', row['user'])

    
    marker=c.df['marks']['grade_calculated'].groupby([c.df['marks']['marker_name']]).mean().reset_index()
    for i, row in marker.iterrows():
        print(row['marker_name'])
        this_team_df=f.filter_row('marks', 'marker_name', row['marker_name'])

        this_count=this_team_df['grade_calculated'].count()
        this_min=this_team_df['grade_calculated'].min()
        this_max=this_team_df['grade_calculated'].max()
        this_std=this_team_df['grade_calculated'].std()
        this_skew=this_team_df['grade_calculated'].skew()

        this_comment_a_wc=this_team_df['comment_a_wc'].mean()
        this_comment_b_wc=this_team_df['comment_b_wc'].mean()
        this_comment_a_sc=this_team_df['comment_a_sc'].mean()
        this_comment_b_sc=this_team_df['comment_b_sc'].mean()
        this_flesch_a=this_team_df['flesch_a'].mean()
        this_flesch_b=this_team_df['flesch_b'].mean()
        
        marker.at[i,'count'] = this_count
        marker.at[i,'min'] = this_min
        marker.at[i,'max'] = this_max
        marker.at[i,'std'] = this_std
        marker.at[i,'skew'] = this_skew
        marker.at[i,'comment_a_wc'] = this_comment_a_wc
        marker.at[i,'comment_b_wc'] = this_comment_b_wc
        marker.at[i,'comment_a_sc'] = this_comment_a_sc
        marker.at[i,'comment_b_sc'] = this_comment_b_sc
        marker.at[i,'flesch_a'] = this_flesch_a
        marker.at[i,'flesch_b'] = this_flesch_b


    print(marker)



        
    #marks['comment_wc'] = len('comment_a')
    #print(marks['comment_wc'])


    # print(type(raw))
    # print(len(raw))
    # print(raw[:75])

    #print(marks.groupby('marker_id', as_index=False).agg({"Grade_Final"}))
    # #iterate through the marks file
    # for i, m_row in marks.iterrows():

    #     print(m_row['marker_name'] + " - " + m_row['marker_id'])
    #     data.groupby(['month', 'item'])['date'].count()


        # # decide whether to use the list_team or list_name field
        # if cfg['feedback_type']['group'] == 'true':
        #     this_record = m_row['list_team']
        # else:
        #     this_record = m_row['user']
        #     this_record_all = m_row['list_name']

        # # define the out files
        # # note that the pdf will be copied as out in wattle_csv.py
        # this_out = c.d['out'] + this_record

        # # display a progress bar in the console
        # # total for progress bar comes from marks.shape[0]
        # f.progress_bar(i, marks.shape[0], this_record)
                

        # #open up a file to print to
        # with open(this_out + '.md', 'w') as out:
            
        #     # create the pandoc header
        #     if cfg['feedback_type']['group'] == 'true':
        #         f.pandoc_header(out, this_record)
        #     else:
        #         f.pandoc_header(out, this_record_all)

        #     if (cfg['crit_display']['text'] == "true") or (cfg['crit_display']['scale'] == "true") or (cfg['crit_display']['graph'] == "true"):
        #         # start with indicator title and notes
        #         print("## " + cfg['pdf_messages']['indicator_title'] + "{-}\n\n", file=out)
        #         print(cfg['pdf_messages']['indicator_note'] + "\n\n", file=out)

        #     #loop through the crit columns
        #     for j, row in crit.iterrows():

        #         # display the fields according to app_config
        #         if (cfg['crit_display']['text'] == "true") or (cfg['crit_display']['scale'] == "true") or (cfg['crit_display']['graph'] == "true"):
        #             f.print_results_header('crit', row, m_row, out)
        #         if cfg['crit_display']['text'] == "true":
        #             f.print_results_text('crit', row, m_row, out)
        #         if cfg['crit_display']['scale'] == "true":
        #             f.print_results_scale('crit', row, m_row, out)
        #         if cfg['crit_display']['graph'] == "true":
        #             f.print_results_graph('crit', row, m_row, out)

        #     # loop through the comment columns
        #     for j, row in comm.iterrows():
        #         f.print_results_header('comm', row, m_row, out)
        #         f.print_results_text('comm', row, m_row, out)

        #     if cfg['crit_display']['rubric'] == "true":
        #         print("# " + cfg['pdf_messages']['rubric_title'] + "{-}\n\n", file=out)
        #         print(cfg['pdf_messages']['rubric_note'] + "\n", file=out)
        #         f.print_results_rubric(out, m_row, this_record)
        #         print("\n", file=out)

        # convert md to pdf using the shell
        #f.pandoc_pdf(this_out)
 
    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
