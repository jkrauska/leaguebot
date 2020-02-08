#!/usr/bin/env python3

"""
Script to dump schedule database to a HTML table for easy presentation on a webpage
Uses datatable library for prettier output.
"""

import dataset
import datafreeze
import csv
from sheetfu import SpreadsheetApp


db = dataset.connect('sqlite:///little-league.db')
teams = db.get_table('teams')
fields = db.get_table('fields')
schedule = db.get_table('schedule')

def dump_html():
    # CSV
    with open('output.csv', 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile)
        # header row
        spamwriter.writerow(schedule.find_one().keys())
        for slot in schedule.all(order_by=['datestamp']):
            spamwriter.writerow(slot.values())


    # HTML
    output = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Schedule Output</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.20/css/jquery.dataTables.css">
    <link rel="stylesheet" type="text/css" href="https://datatables.net/media/css/site-examples.css">
    </head>

    <body>
    <table id="example" class="display" style="width:100%">
    <thead>
    <tr>"""

    for header in schedule.find_one().keys():
        output += f"<th>{header}</th>"
    output+="</tr>\n</thead>\n"

    output+="<tbody>\n"
    for slot in schedule.all(order_by=['datestamp']):
        output+='<tr>'
        for column in slot.values():
            output+=f"<td>{column}</td>"
        output+="</tr>\n"

    output+="""
    </tbody>
    </table>
    <script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.3.1.js"></script>
    <script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.20/js/jquery.dataTables.min.js"></script>
    <script>
    $(document).ready(function() {
        $('#example').DataTable( {
            "order": [[ 7, "asc" ]],
            "lengthMenu": [[25, 50, 100, -1], [25, 50, 100, "All"]],
            "columnDefs": [
                {
                    "targets": [ 0, 2 ],
                    "visible": false,
                    "searchable": false
                }
            ]
        } );
    } );
    </script>
    </body>
    </html>
    """

    html = open("output.html", 'w')
    html.write(output)


def set_header(output=[]):
    output=[]
    header = list(schedule.find_one().keys())
    output.append(header)
    return(output)

def get_divisions():
    return([ team['division_name'] for team in teams.distinct('division_name')])


def get_teams(division):
    return([ team['team_name'] for team in teams.distinct('team_name', division_name=division)])


def get_games(division, team):
    print('Getting games for %s %s' % (division, team))
    myoutput=[]
    for slot in schedule.find(division=division, order_by=['datestamp']):
        if team == slot['home_team'] or team == slot['away_team']:
            myoutput.append(list(slot.values()))
    print('Found %s' % len(myoutput))
    if len(myoutput) > 0:
        return(myoutput)
    else:
        return([])

def publish_data(myoutput, sheet_name='NEW'):
    try:
        spreadsheet.create_sheets(sheet_name)
    except:
        pass

    sheet = spreadsheet.get_sheet_by_name(sheet_name)

    data_range = sheet.get_range(row=1, 
                                column=1, 
                                number_of_row=len(myoutput),
                                number_of_column=(len(myoutput[0])))

    data_range.set_values(myoutput)



# Google Sheet
sa = SpreadsheetApp('secret.json')
spreadsheet = sa.open_by_id('12BDEIWO_85BN6egolnUqIpHQ6yRPyx35VnccSCQD2Ag')


# Full data
output=[]
for slot in schedule.all(order_by=['datestamp']):
    output.append(list(slot.values()))
publish_data(output, 'NEW')


for division in get_divisions():


    print('='*80)
    print(division)


    output_by_division = []
    output_by_division = set_header()

    for team in get_teams(division):
        colcount = len(list(schedule.find_one().keys()))
        output_by_division += [[team] * colcount]  # newline
        print(('-'*80))
        print(team)
        mygames = get_games(division, team)

        output_by_division += mygames
        print('Size of divsion data: %s' % len(output_by_division))

    print('Publishing %s' % division)
    publish_data(output_by_division, sheet_name=division)
