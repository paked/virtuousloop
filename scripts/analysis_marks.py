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
from wordcloud import WordCloud
import subprocess
import matplotlib.pyplot as plt
import json
import numpy as np


def analysis_marks():

    cfg = f.load_config()

    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))
    f.pnt_info(c.msg["console_loading"])

    marks_df = f.load_tsv('marks')
    crit_levels = f.load_tsv('crit_levels')

    # create a df of just the crit and the comments
    crit = f.filter_row('fields', 'field', 'crit_')
    comm = f.filter_row('fields', 'field', 'comment_')

    crit_list = f.create_list(crit, 'field')
    comment_list = f.create_list(comm, 'field')

    f.pnt_info(c.msg["console_creating_feedback_files"])
    # clean up marks df
    c.df['marks'].loc[c.df['marks'].grade_final == 0, ['marker_name', 'marker_id']] = 'No_Submission', 'nil'

    for comment in comment_list:
        c.df['marks'][comment + "_txt"] = c.df['marks'][comment].apply(f.html_to_text)

    f.pnt_console("Processing the marks file")
    for i, row in c.df['marks'].iterrows():
        for comment in comment_list:
            for readability_list in cfg['analytics']['readability_stats']:
                f.readability_stats('marks', row, i, comment + '_txt', comment + "_" + readability_list[0], readability_list[1], readability_list[2])

    c.df['marks']['grade_final_pct'] = ( c.df['marks']['grade_final'] / int(cfg['assignment']['grade_final_out_of']) * 100 )
    c.df['marks']['diff_final_sugg'] = (c.df['marks']['grade_final_pct'] - c.df['marks']['grade_suggested']).round(decimals=1)
    c.df['marks']['diff_calc_sugg'] = (c.df['marks']['grade_calculated'] - c.df['marks']['grade_suggested']).round(decimals=1)

    # generate a dataframe with the readability stats for each marker
    # then replace any nil submissions with 'no submission'
    marker = c.df['marks']['grade_final'].groupby([c.df['marks']['marker_name']]).mean().reset_index()
    marker = marker[marker.marker_name != 'No_Submission']
    # create a marker_list for iteration
    marker_list = f.create_list(marker, 'marker_name')

    f.pnt_info("Building crit graphs...")
    # work through each criterion
    for criterion in crit_list:
        # print to tho console
        print(criterion)
        this_crit_df = crit_levels['index']
        for i, row in marker.iterrows():

            this_marker_name = row['marker_name']
            this_marker_df = f.filter_row('marks', 'marker_name', this_marker_name)
            this_marker_stats = f.make_crit_list(crit, this_marker_df)
            
            this_col_sum = this_marker_stats[criterion].sum()
            this_marker_stats[this_marker_name] = this_marker_stats[criterion].apply(lambda x: x/this_col_sum*100)
            this_crit_df = pd.merge(this_crit_df, this_marker_stats[this_marker_name], on='index')
        
        this_crit_df['average'] = this_crit_df.mean(axis=1)
        this_crit_df = this_crit_df.set_index('index')
        f.make_count_chart(this_crit_df, criterion)


    bin_values = [-10, -5.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 5.5, 10]
    bin_labels = [-10, -5, -2, -1, 0, 1, 2, 5, 10]

    calc_sugg_df = pd.DataFrame(bin_labels,columns=['bin'])
    final_sugg_df = pd.DataFrame(bin_labels,columns=['bin'])

    c.df['marks']['bin_calc_sugg'] = pd.cut(c.df['marks']['diff_calc_sugg'], bins=bin_values, labels=bin_labels)
    c.df['marks']['bin_final_sugg'] = pd.cut(c.df['marks']['diff_final_sugg'], bins=bin_values, labels=bin_labels)

    for i, row in marker.iterrows():
        this_marker_name = row['marker_name']
        this_marker_df = f.filter_row('marks', 'marker_name', this_marker_name)

        this_marker_calc_df = pd.DataFrame(this_marker_df.bin_calc_sugg.value_counts()).reset_index()
        this_marker_calc_df = this_marker_calc_df.rename(columns={'index': 'bin'})

        this_col_sum = this_marker_calc_df['bin_calc_sugg'].sum()
        this_marker_calc_df[this_marker_name] = this_marker_calc_df['bin_calc_sugg'].apply(lambda x: x/this_col_sum*100)
        this_marker_calc_df = this_marker_calc_df.drop(['bin_calc_sugg'], axis=1)
        diff_calc_sugg_df = pd.merge(calc_sugg_df, this_marker_calc_df, on='bin')
        calc_sugg_df = diff_calc_sugg_df.set_index("bin")

    f.make_count_chart(calc_sugg_df, 'suggested')

    f.pnt_info("Analysing each marker...")

    for i, row in marker.iterrows():
        this_marker_name = row['marker_name']
        print(this_marker_name)
        this_group_df=f.filter_row('marks', 'marker_name', row['marker_name'])

        marker.at[i, 'grade_count'] = this_group_df['grade_final'].count()
        marker.at[i, 'grade_mean'] = this_group_df['grade_final'].mean()
        marker.at[i, 'grade_min'] = this_group_df['grade_final'].min()
        marker.at[i, 'grade_max'] = this_group_df['grade_final'].max()
        marker.at[i, 'grade_std'] = this_group_df['grade_final'].std()
        marker.at[i, 'grade_skew'] = this_group_df['grade_final'].skew()

        # generate the readability stats
        for comment in comment_list:
            for readability_list in cfg['analytics']['readability_stats']:
                marker.at[i, comment + "_" + readability_list[0]] = this_group_df[comment + "_" + readability_list[0]].mean()

            # get the comment to pass to the nlp
            this_comment = " ".join(f.create_list(this_group_df, comment + "_txt"))

            # store the comment so that it can be accessed for the word cloud
            with open(c.d['txt'] + this_marker_name + "_" + comment + ".txt", 'w') as out:
                print(this_comment, file=out)

            this_nlp_file = Path(c.d['nlp'] + this_marker_name + "_" + comment + ".json")
            # check if the nlp data already exists
            # this is important only to reduce the numbers of calls on the api for local testing
            if not this_nlp_file.is_file():
                # get the results from the api
                this_nlp = f.text_analysis_api(this_comment, 'comment', row['marker_name'])
                with open(this_nlp_file, 'w') as out:
                    print(this_nlp, file=out)

            # create a wordcloud using the wordcloud_cli interface
            subprocess.call("wordcloud_cli --width 1000 --height 250 --text " + c.d['txt'] + this_marker_name + "_" + comment + ".txt --imagefile " + c.d['wordcloud'] + this_marker_name + "_" + comment + ".png --fontfile ./includes/fonts/Roboto-Medium.ttf --background white --color blue", shell=True)

        # open a file to write to for each marker
        # this will be joined to the end of the analysis
        with open(c.d['md'] + this_marker_name + '.md', 'w') as out:
            print("\n\n## Analysis of " + this_marker_name + "'s Feedback\n\n", file=out)

        # using enumerate to access list indices for name and title
        # work through the defined nlp endpoints
        for num, endpoint in enumerate(cfg['aylien']['endpoints'], start=0):
            name = (cfg['aylien']['endpoint_name'][num])
            title = (cfg['aylien']['endpoint_title'][num])
            
            # treat sentiment differently, as it is better presented in a table
            if endpoint != 'sentiment':
                with open(c.d['md'] + this_marker_name + '.md', 'a') as out:
                    print("\n### Comment " + title + "\n\n", file=out)
                    print("\n*" + cfg['analytics']['nlp_source_comment']+  "*\n", file=out)

                    # loop through the analysis for each comment
                    for i, row in comm.iterrows():
                        comment = row['field']
                        field_text = row['label']

                        # load the nlp json response to read from
                        with open(c.d['nlp'] + this_marker_name + "_" + comment + ".json") as json_file:
                            this_nlp = json.load(json_file)

                            # print a header to out
                            print("\n**" + title + " for " + field_text + "**" "\n\n", file=out)
                            try: 
                                item_out = ""
                                for item in this_nlp[name]:
                                    item_out = item.replace("#", "\\#")
                                    print("* " + item_out, file=out)
                            except:
                                print("* N/A", file=out)
    
    # create a stat_chart for the marker means
    f.make_stat_chart(marker, 'marker_name', 'grade_mean', 'grade_mean')


    # work through the readability stats to create a chart
    for readability_list in cfg['analytics']['readability_stats']:

        columns_old = ['marker_name']
        columns_new = ['marker_name']

        for i, row in comm.iterrows():
            field = row['field']
            text = row['label']
            columns_old.append(field + "_" + readability_list[0])
            columns_new.append(text)

        this_marker = marker[columns_old].copy()
        this_marker.columns = columns_new
        f.make_stat_chart(this_marker, 'marker_name', columns_new, readability_list[0])

    # start by creating a file to compile everything into
    with open(c.d['md'] + cfg['analytics']['filename'] + ".md", 'w') as out:
        # header 1
        print("## " + cfg['analytics']['analytics_header'] + "\n\n", file=out)
        # header for summary data
        print("### " + cfg['analytics']['grade_table_header'] + "\n\n", file=out)
        print("![](../../." + c.d['charts'] + "grade_mean.png)\n\n", file=out)
        print("*" + cfg['analytics']['grade_chart_comment']+ "*\n\n", file=out)
        print("### " + cfg['analytics']['grade_table_header'] + "\n\n", file=out)
        print("*" + cfg['analytics']['grade_table_comment']+ "*\n\n", file=out)

        # create a summary table for display
        marker_html = marker[['marker_name','grade_count','grade_final','grade_std','grade_min','grade_max','grade_skew']].round(1)
        marker_html.columns = ['Marker', 'Count', 'Mean', 'StDev', 'Min', 'Max', 'Skew']
        marker_html.set_index('Marker', inplace=True)
        print(marker_html.to_html(), file=out)
        
        print("## Difference between suggested and calculated grade \n\n", file=out)
        print("*This highlights the tendancy of markers to drift from the suggested mark provided in the Database*\n\n", file=out)
        print("![](../../." + c.d['charts'] + "count_suggested.png)\n\n", file=out)
        print("*Y-axis values are normalised.*\n\n", file=out)

        print("# " + cfg['analytics']['rubric_header'] + "\n\n", file=out)
        for loop_row in crit.itertuples():
            criterion = loop_row.field
            f.print_results_header(loop_row, out)
            print('*' + cfg['analytics']['rubric_comment']+ '*\n\n', file=out)
            print("![](../../." + c.d['charts'] + "count_" + criterion + ".png)\n\n", file=out)
            print("*Y-axis values are normalised.*\n\n", file=out)

        print("# " + cfg['analytics']['readability_header'] + "\n\n", file=out)
        for readability_list in cfg['analytics']['readability_stats']:
            print("\n\n### " + cfg['crit_chart'][readability_list[0]], file=out)
            print("![](../../." + c.d['charts']  + readability_list[0] + ".png)\n\n", file=out)
            print("*" + cfg['crit_chart'][readability_list[0]] + cfg['analytics']['readability_comment'] + "*\n\n", file=out)
        
        print("\n\n# " + cfg['analytics']['sentiment_header'] + "\n\n", file=out)

        sentiment_df = f.sentiment_table(comm, marker)
        sentiment_df.set_index('Name', inplace=True)
        print(sentiment_df.to_html(), file=out)

        print("# " + cfg['analytics']['summary_header']+ "\n\n", file=out)

    # combine the individual marker files
    with open(c.d['md'] + cfg['analytics']['filename'] + '.md', 'a') as out_file:
        for i, row in marker.iterrows():
            this_marker_name = row['marker_name']
            print(this_marker_name)
            with open(c.d['md'] + this_marker_name + '.md') as in_file:
                out_file.write(in_file.read())

    with open(c.d['md'] + cfg['analytics']['filename'] + '.md', 'a') as out:
        print("\n\n\n\n*** **END OF ANALYSIS** ***\n\n", file=out)

    with open(c.d['yaml'] + cfg['analytics']['filename'] + '.yaml', 'w') as out:
        f.pandoc_yaml(out, cfg['analytics']['filename'])
        
    with open(c.d['css'] + cfg['analytics']['filename'] + ".css", 'w') as out:
        f.pandoc_css(out, cfg['analytics']['filename'], 'anon')

    f.pandoc_html_single(cfg['analytics']['filename'])
    f.pandoc_pdf(cfg['analytics']['filename'])

    f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))
