#!/usr/bin/env python3
# python ./scripts/feedback_tmc.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the data_tmc csv into pdf feedback'''

import os
import re
from pandas import DataFrame
import matplotlib.pyplot as plt
import glob
import config as c
import functions as f
from PyPDF2 import PdfFileMerger

# silence matplot warnings
plt.rcParams.update({'figure.max_open_warning': 0})


# main loop
def feedback_tmc():
    
    cfg = f.load_config()

    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))
    f.pnt_info(c.msg["console_loading"])
    
    teams = f.load_tsv('data_tmc')
    teams.drop_duplicates(subset=['list_team'], keep='first', inplace=True)
    teams = teams['list_team']

    data_tmc = f.load_tsv('data_tmc')
    data_tmc.replace(cfg['tmc_chart']['find_labels'], cfg['tmc_chart']['replace_values'], inplace=True) 
    
    tm_cols_tmc = [col for col in data_tmc.columns if 'contribution' in col]
    tm_cols_tmc.sort()
    tm_cols_tmc.insert(0,'username')
    tm_cols_id = [w.replace('contribution', 'id') for w in tm_cols_tmc]

    f.pnt_info(c.msg["console_tmc"])
    
    print(data_tmc)

    for team in teams: 
        print(team)

        this_data=f.filter_row('data_tmc', 'list_team', team)
        print(this_data)

        team_header=this_data[tm_cols_id].values.tolist()[0]
        team_header[0]='reviews'

        team_data=this_data[tm_cols_tmc].values.tolist()
        
        this_conf_df=DataFrame.from_records(team_data, columns=team_header).set_index('reviews').dropna(axis=1, how='all')
        print(this_conf_df)
        this_conf_df=this_conf_df.rename(columns=lambda x: re.sub(' - .*','',x)).T
        print(this_conf_df)
        this_anon_df=this_conf_df.rename(columns=lambda x: re.sub('u.*',cfg['tmc_chart']['anon_legend'],x))
        
        shape=this_anon_df.shape

        this_anon_df['average'] = this_anon_df.mean(axis=1)
        this_conf_df['average'] = this_conf_df.mean(axis=1)

        f.make_tmc_chart(this_anon_df, c.d['charts'] + team + "_tmc_anon.png")
        f.make_tmc_chart(this_conf_df, c.d['charts'] + team + "_tmc_conf.png")

        format_tmc_feedback(team, 'conf', shape, this_data)
        format_tmc_feedback(team, 'anon', shape, this_data)

    f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))

    all_conf = glob.glob(c.d['pdf'] + '/*_conf.pdf')
    all_conf.sort()
    merger = PdfFileMerger()
    for pdf in all_conf:
        merger.append(pdf)
    merger.write(c.f['all_conf'])
    merger.close()


# print feedback loop
def format_tmc_feedback(team, kind, shape, dataframe):
    cfg = f.load_config()

    this_df=dataframe.copy() 
    this_df.fillna('',inplace=True)

    this_out=team + "_tmc_" + kind

    with open(c.d['yaml'] + team + '.yaml', 'w') as out:
        f.pandoc_yaml(out, team)

    # open and create a file for the css
    with open(c.d['css'] + team + "_" + kind + '.css', 'w') as out:
        f.pandoc_css(out, team, kind)

    # open and create a file for the md
    with open(c.d['md'] + this_out + ".md", 'w') as out:
        this_chart=c.d['charts'] + team + "_tmc_" + kind + ".png"

        print("\n\n## " + cfg['pdf_messages']['tmc_header_1'] + "\n\n", file=out)
        print("\n\n## " + cfg['tmc_pdf']['eval_header'] + "\n\n", file=out)
        if ( cfg['tmc_pdf']['team_count_message'] == "true" ):
            print("**" + str(shape[1]) + "**" + " out of **" + str(shape[0]) + "** " + cfg['tmc_pdf']['count_message'] + "\n\n", file=out)

        print('![](../../.' + this_chart + ')\n\n', file=out)
        print( cfg['tmc_pdf']['tmc_chart_caption'] + "\n\n", file=out )

        print("## " + cfg['pdf_messages']['tmc_header_2'] + "\n\n", file=out)
        for i, df_row in this_df.iterrows():
            if (df_row['teamcomments'] == ""):
                if ( kind == 'conf'):
                    print("**" + df_row['user'] + " (" + df_row['username'] + ")" + "**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                else:
                    print("**" + cfg['tmc_pdf']['member_header'] + "**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
            else:
                if ( kind == 'conf'):
                    print("**" + df_row['user'] + " (" + df_row['username'] + ")" + "**\n\n" + str(df_row['teamcomments']) + "\n\n", file=out)
                else:
                    print("**" + cfg['tmc_pdf']['member_header'] + "**\n\n" + str(df_row['teamcomments']) + "\n\n", file=out)

        # print confidential comments
        if ( kind == 'conf'):
            print("## " + cfg['pdf_messages']['tmc_confidential'] + "\n\n", file=out)
            for i, df_row in this_df.iterrows():
                if (df_row['teamcomments'] == ""):
                    print(df_row['confidentialcomments'])
                    print("**" + df_row['user'] + " (" + df_row['username'] + ")" + "**\n\n" + cfg['tmc_pdf']['member_no_comment'] + "\n\n", file=out)
                else:
                    print("**" + df_row['user'] + " (" + df_row['username'] + ")" + "**\n\n" + str(df_row['confidentialcomments']) + "\n\n", file=out)

    # convert md to pdf using the shell
    f.pandoc_html(this_out, team, kind)
    f.pandoc_pdf(this_out)
