#!/usr/bin/env python3
# python ./scripts/feedback_marks.py
#
#
# chris.browne@anu.edu.au - all care and no responsibility :)
# ===========================================================

'''turns the marks spreadsheet into pdf feedback'''
'''expects one submission per row'''

import os
import config as c
import functions as f
from jinja2 import Template, Environment, FileSystemLoader

template_dir = c.d['jinja']
env = Environment(loader=FileSystemLoader(template_dir))

def feedback_marks():

    cfg = f.load_config()
    f.pnt_notice(c.msg['console_start'], os.path.basename(__file__))
    f.pnt_info(c.msg["console_loading"])
    
    # load in tsvs of needed fields
    marks_df = f.load_tsv('marks')
    marks_dict = marks_df.to_dict(orient='index')

    # create a df of just the crit for manipulation
    crit_df = f.filter_row('fields', 'field', 'crit_')
    crit_dict = crit_df.to_dict(orient='index')

    levels_df = f.load_tsv('crit_levels')
    levels_dict = levels_df.to_dict(orient='index')

    field_df = f.delete_duplicates('fields', crit_df)
    field_dict = field_df.to_dict(orient='index')

    f.pnt_info(c.msg["console_creating_feedback_files"])
    
    # create distribution charts for later
    if cfg['crit_display']['graph']:
        stats = f.make_crit_list(crit_df, marks_df)
        f.make_crit_chart(crit_df, stats, "na")

    ## need to figure out display of the rubric if applicable - probably html->pdf here

    print(cfg)
    print(crit_dict)
    print(levels_dict)

    # iterate through the marks file
    for record in marks_dict.values():
        print(record)
        # evaluate whether to use the list_team or list_name field
        if cfg['feedback_type']['group']:
            this_record = record['list_team']
            this_record_name = record['list_team']
        else:
            this_record = record['user']
            this_record_name = record['list_name']

        template = env.get_template("feedback_marks.html")
        with open(c.d['html'] + this_record + '.html', 'w') as out:
            out.write(template.render(
                record=record,
                record_name=this_record_name,
                options_dict=cfg,
                field_dict=field_dict,
                crit_dict=crit_dict,
                levels_dict=levels_dict,
            ))

        f.weasy_pdf(this_record)

    f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))

    #
    #
    #     # # create the pandoc header
    #     # with open(c.d['yaml'] + this_record + '.yaml', 'w') as out:
    #     #     f.pandoc_yaml(out, this_record_name)
    #     #
    #     # with open(c.d['css'] + this_record + '.css', 'w') as out:
    #     #     f.pandoc_css(out, this_record_name, 'anon')
    #
    #     #open up a file to print to
    #     with open(c.d['md'] + this_record + '.md', 'w') as out:
    #         print("## " + cfg['pdf_messages']['comment_title'] + "{-}\n\n", file=out)
    #         for loop_row in comm.itertuples():
    #             f.print_results_header(loop_row, out)
    #             f.print_results_text(loop_row, record_row, out)
    #
    #         #loop through the crit columns according to app_config
    #         if cfg['crit_display']['text']\
    #             or cfg['crit_display']['scale']\
    #             or cfg['crit_display']['graph']:
    #
    #             # start with indicator title and notes
    #             print("# " + cfg['pdf_messages']['indicator_title'] + "{-}\n\n", file=out)
    #             print(cfg['pdf_messages']['indicator_note'] + "\n\n", file=out)
    #             print(cfg['pdf_messages']['chart_note'] + "\n\n", file=out)
    #
    #         for loop_row in crit.itertuples():
    #             if cfg['crit_display']['text'] \
    #                 or cfg['crit_display']['scale'] \
    #                 or cfg['crit_display']['graph']:
    #                 f.print_results_header(loop_row, out)
    #             if cfg['crit_display']['text']:
    #                 f.print_results_text(loop_row, record_row, out)
    #             if cfg['crit_display']['scale']:
    #                 f.print_results_scale(loop_row, record_row, out)
    #             if cfg['crit_display']['graph']:
    #                 f.print_results_graph(loop_row, record_row, out)
    #             # if cfg['crit_display']['rubric_new_page']:
    #             #     f.print_new_page(out)
    #
    #         if cfg['crit_display']['rubric']:
    #             if cfg['rubric_display']['rubric_new_page']:
    #                 print("# " + cfg['pdf_messages']['rubric_title'] + "{-}\n\n", file=out)
    #             else:
    #                 print("## " + cfg['pdf_messages']['rubric_title'] + "{-}\n\n", file=out)
    #             print(cfg['pdf_messages']['rubric_note'] + "\n", file=out)
    #             f.print_results_rubric(record_row, this_record)
    #             print("\n", file=out)
    #
    #     f.pandoc_html_single(this_record)
    #
    #     # add the rubric
    #     if cfg['crit_display']['rubric']:
    #         files = [c.d['rubric'] + this_record + ".html"]
    #         with open(c.d['html'] + this_record + '.html', 'a') as outfile:
    #             for fname in files:
    #                 with open(fname) as infile:
    #                     outfile.write(infile.read())
    #
    #     f.pandoc_pdf(this_record)
    #
    # # print message to console - complete!
    # f.pnt_notice(c.msg['console_complete'], os.path.basename(__file__))
