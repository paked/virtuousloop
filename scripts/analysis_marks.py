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


def analysis_marks():
    
    # check that config exists
    cfg=f.config_exists()
    print(cfg)

    print("****" + cfg['assignment']['assignment_title'])
    
    # print message to console - starting!
    f.pnt_notice(c.msg['console_start'],os.path.basename(__file__))

    # print message to console
    f.pnt_info(c.msg["console_loading"])
    
    # load in tsvs of needed fields
    #fields=f.load_tsv('fields')
    marks_df=f.load_tsv('marks')

    crit_levels=f.load_tsv('crit_levels')

    # create a df of just the crit and the comments
    crit=f.filter_row('fields', 'field', 'crit_')
    comm=f.filter_row('fields', 'field', 'comment_')

    crit_list=f.create_list(crit, 'field')
    comment_list=f.create_list(comm, 'field')

    # print message to console
    f.pnt_info(c.msg["console_creating_feedback_files"])

    # clean up marks df
    c.df['marks'].loc[c.df['marks'].grade_calculated == 0, ['marker_name', 'marker_id']] = 'No_Submission', 'nil'

    # create a new column with the text
    for i, row in c.df['marks'].iterrows():
        for comment in comment_list:
            f.html_to_text('marks', row, i, comment, comment + "_txt")

    # gather the readability stats from each comment
    for i, row in c.df['marks'].iterrows():
        print(row['user'])
        for comment in comment_list:
            for readability_list in cfg['analytics']['readability_stats']:
                f.readability_stats('marks', row, i, comment + '_txt', comment + "_" + readability_list[0], readability_list[1], readability_list[2])

    # generate a dataframe with the readability stats for each marker
    # then replace any nil submissions with 'no submission'
    marker=c.df['marks']['grade_calculated'].groupby([c.df['marks']['marker_name']]).mean().reset_index()
    marker=marker[marker.marker_name != 'No_Submission']

    # create a marker_list for iteration
    marker_list=f.create_list(marker, 'marker_name')

    # work through each criterion
    for criterion in crit_list:
        # print to tho console
        print(criterion)
        this_crit_df = crit_levels['index']
        for i, row in marker.iterrows():
            # create the stats for each marker
            this_marker_name=row['marker_name']
            # get only the rows for this marker
            this_marker_df=f.filter_row('marks', 'marker_name', this_marker_name)
            # turn the stats for the marker into a df
            this_marker_stats=f.make_crit_list(crit, this_marker_df)
            # get the sum of the column for the stats so that the value can be given as a percentage
            this_col_sum=this_marker_stats[criterion].sum()
            # add the column
            this_marker_stats[this_marker_name] = this_marker_stats[criterion].apply(lambda x: x/this_col_sum*100)
            # merge back to the crit_df
            this_crit_df = pd.merge(this_crit_df, this_marker_stats[this_marker_name], on='index')
        
        # provide a mean value for the graph
        this_crit_df['average'] = this_crit_df.mean(axis=1)
        # generate a chart for the criterion
        f.make_feedback_chart(this_crit_df, c.d['charts'] + criterion + ".png")


    # work through each marker
    for i, row in marker.iterrows():
        this_marker_name=row['marker_name']
        # print to the console
        print(this_marker_name)

        # get the relevant rows for the analysis
        this_group_df=f.filter_row('marks', 'marker_name', row['marker_name'])

        marker.at[i, 'grade_count'] = this_group_df['grade_calculated'].count()
        marker.at[i, 'grade_mean'] = this_group_df['grade_calculated'].mean()
        marker.at[i, 'grade_min'] = this_group_df['grade_calculated'].min()
        marker.at[i, 'grade_max'] = this_group_df['grade_calculated'].max()
        marker.at[i, 'grade_std'] = this_group_df['grade_calculated'].std()
        marker.at[i, 'grade_skew'] = this_group_df['grade_calculated'].skew()

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
                this_nlp=f.text_analysis_api(this_comment, 'comment', row['marker_name'])
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
            name=(cfg['aylien']['endpoint_name'][num])
            title=(cfg['aylien']['endpoint_title'][num])
            
            # treat sentiment differently, as it is better presented in a table
            if endpoint != 'sentiment':
                with open(c.d['md'] + this_marker_name + '.md', 'a') as out:
                    print("\n### Comment " + title + "\n\n", file=out)
                    print("\n*" + cfg['analytics']['nlp_source_comment']+  "*\n", file=out)
                    # layout side-by-side (not working with weasyprint @ todo)
                    print("<article id=\"columns\"><section>", file=out)

                    # loop through the analysis for each comment
                    for i, row in comm.iterrows():
                        comment = row['field']
                        field_text = row['text']

                        # load the nlp json response to read from
                        with open(c.d['nlp'] + this_marker_name + "_" + comment + ".json") as json_file:
                            this_nlp = json.load(json_file)

                            # print a header to out
                            print("\n**" + title + " for " + field_text + "**" "\n\n", file=out)
                            try: 
                                item_out = ""
                                for item in this_nlp[name]:
                                    # replace hashes so that they are not interpreted in markdown
                                    item_out = item.replace("#", "\\#")
                                    # print to out each item in a list
                                    print("* " + item_out, file=out)
                            except:
                                # if there's nothing there, print N/A
                                print("* N/A", file=out)
                    # close out the section (not working with weasyprint)
                    print("</section></article>", file=out)
    # done with marker
    
    # create a stat_chart for the marker means
    f.make_stat_chart(marker, 'marker_name', 'grade_mean', 'grade_mean')

    # work through the readability stats to create a chart
    for readability_list in cfg['analytics']['readability_stats']:
        # geerate a df to te turn into a stat_chart
        columns_old=['marker_name']
        columns_new=['marker_name']
        # show results for different comments side-by-side
        for i, row in comm.iterrows():
            field=row['field']
            text=row['text']
            columns_old.append(field + "_" + readability_list[0])
            # get the human readabile value for titles in the chart
            columns_new.append(text)
        # make a copy of the the marker df to get start
        this_marker = marker[columns_old].copy()
        # replace the columns with the human readable values
        this_marker.columns = columns_new
        # generate the stat chart for the readability value
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
        marker_html = marker[['marker_name','grade_count','grade_calculated','grade_std','grade_min','grade_max','grade_skew']].round(1)
        marker_html.columns = ['Marker', 'Count', 'Mean', 'StDev', 'Min', 'Max', 'Skew']
        marker_html.set_index('Marker', inplace=True)
        print(marker_html.to_html(), file=out)
        
        # print the table to console for assurance
        print(marker_html)

        # header for rubric data
        print("# " + cfg['analytics']['rubric_header'] + "\n\n", file=out)

        # iterate through the criteria
        for j, row in crit.iterrows():
            # display the fields according to app_config
            f.print_results_header('crit', row, row, out)
            print('*' + cfg['analytics']['rubric_comment']+ '*', file=out)
            f.print_results_graph('crit', row, row, out)

        # header for readability data
        print("# " + cfg['analytics']['readability_header'] + "\n\n", file=out)
        for readability_list in cfg['analytics']['readability_stats']:
            print("\n\n### " + cfg['crit_chart'][readability_list[0]], file=out)
            print("![](../../." + c.d['charts']  + readability_list[0] + ".png)\n\n", file=out)
            print("*" + cfg['crit_chart'][readability_list[0]] + cfg['analytics']['readability_comment'] + "*\n\n", file=out)
        
        # header for sentiment_analysis
        print("\n\n# " + cfg['analytics']['sentiment_header'] + "\n\n", file=out)

        # generate a table extracting sentiment analysis
        # then print the sentiment

        sentiment_df = f.sentiment_table(comm, marker)
        sentiment_df.set_index('Name', inplace=True)
        print(sentiment_df.to_html(), file=out)

        # header for data extracted
        print("# " + cfg['analytics']['summary_header']+ "\n\n", file=out)

    # combine the individual marker files
    with open(c.d['md'] + cfg['analytics']['filename'] + '.md', 'a') as out_file:
        for i, row in marker.iterrows():
            this_marker_name=row['marker_name']
            print(this_marker_name)
            with open(c.d['md'] + this_marker_name + '.md') as in_file:
                out_file.write(in_file.read())

    # create the weasyprint variables
    with open(c.d['yaml'] + cfg['analytics']['filename'] + '.yaml', 'w') as out:
        f.pandoc_yaml(out, cfg['analytics']['filename'])
        
    # create the weasyprint stylesheet
    with open(c.d['css'] + cfg['analytics']['filename'] + ".css", 'w') as out:
        f.pandoc_css(out, cfg['analytics']['filename'], 'anon')

    # turn the pandoc md to html to pdf
    f.pandoc_html_single(cfg['analytics']['filename'])
    f.pandoc_pdf(cfg['analytics']['filename'])

    # print message to console - complete!
    f.pnt_notice(c.msg['console_complete'],os.path.basename(__file__))
