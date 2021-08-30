#!/usr/bin/env python3

"""
Script to dump schedule database to a HTML table for easy presentation on a webpage
Uses datatable library for prettier output.
"""

import dataset
import datafreeze
import csv
from sheetfu import SpreadsheetApp
from collections import OrderedDict, Counter


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
    #print('Getting games for %s %s' % (division, team))
    myoutput=[]
    for slot in schedule.find(division=division, order_by=['datestamp']):
        if team == slot['home_team'] or team == slot['away_team']:
            myoutput.append(list(slot.values()))
    #print('Found %s' % len(myoutput))
    if len(myoutput) > 0:
        return(myoutput)
    else:
        return([])

def publish_data(myoutput, sheet_name='FULL'):
    print('Publishing %s' % sheet_name)

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
spreadsheet = sa.open_by_id('19oc67iPOkwvxSbDuNwXyK2OPezt2ZiSO5-K7QAc5TJM')
                            #  19oc67iPOkwvxSbDuNwXyK2OPezt2ZiSO5-K7QAc5TJM/

# Full data set 
output = []
output = set_header()

count=1
for slot in schedule.all(order_by=['datestamp']):
    #print(count, slot)
    count+=1
    output.append(list(slot.values()))
output.append(['XXX']*20)
publish_data(output, 'FULL')



# By division data 
for division in get_divisions():

    output_by_division = []
    output_by_division = set_header()

    for team in get_teams(division):
        colcount = len(list(schedule.find_one().keys()))
        new_line = [''] * 1 +  [team] + [''] * (colcount-2)
        #print(new_line)
        output_by_division.append(new_line)  # newline

        mygames = get_games(division, team)
        output_by_division += mygames
    output_by_division.append(['XXXX'] * colcount)
    publish_data(output_by_division, sheet_name=division)


# unused slots
output_unused = []
output_unused = set_header()
for slot in schedule.find(division=None, order_by=['datestamp']):
    output_unused.append(list(slot.values()))

output_unused.append(['XXXX'] * colcount)

publish_data(output_unused, 'UNUSED')


# Build analysis
team_counters=OrderedDict()
for slot in schedule.all():
    for team in [slot['home_team'], slot['away_team']]:
        if team is not None:

            division_and_team = '%s,%s' % (slot['division'], team)
            #print(division_and_team)

            if division_and_team not in team_counters:
                team_counters[division_and_team] = Counter()
                # Init
                for dow in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                    team_counters[division_and_team][dow] = 0
                for category in ['total', 'home', 'away', 'turf', 'grass', 'TI', 'SF', 'M-F-TI', 'SS-TI', 'M-F-SF', 'SS-SF', 'Tepper', 'Ketcham', 'Ft. Scott', 'Kimbell', 'SouthSunset', 'Paul Goode', 'Tepper Home', 'Tepper Away' ]:
                    team_counters[division_and_team][category] = 0

            if team == slot['home_team']:
                team_counters[division_and_team]['home'] += 1
                if 'Tepper' in slot['field']:
                    team_counters[division_and_team]['Tepper Home'] += 1
            elif team == slot['away_team']:
                team_counters[division_and_team]['away'] += 1
                if 'Tepper' in slot['field']:
                    team_counters[division_and_team]['Tepper Away'] += 1


            team_counters[division_and_team]['total'] += 1

            team_counters[division_and_team][slot['type']] += 1
            team_counters[division_and_team][slot['location']] += 1
            team_counters[division_and_team][slot['day_of_week']] += 1

            if slot['day_of_week'] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                team_counters[division_and_team][f"M-F-{slot['location']}" ] += 1
            else:
                #print(slot)
                team_counters[division_and_team][f"SS-{slot['location']}" ] += 1

            if slot['field'] in ['Tepper', 'Ketcham']:
                team_counters[division_and_team][slot['field']] += 1
            elif 'Ft. Scott' in slot['field']:
                team_counters[division_and_team]['Ft. Scott'] += 1
            elif 'Kimbell' in slot['field']:
                team_counters[division_and_team]['Kimbell'] += 1
            elif 'SouthSunset' in slot['field']:
                team_counters[division_and_team]['SouthSunset'] += 1
            elif 'Paul Goode' in slot['field']:
                team_counters[division_and_team]['Paul Goode'] += 1
            



analysis = []
header = []
for team in sorted(team_counters.keys()):
    header.append('division')
    header.append('team')
    #print(f"divsion,team,", end='')
    for value, count in team_counters[team].items():
        header.append(value)
        #print(f'{value},', end='')
    #print('')
    break
analysis.append(header)

for team in sorted(team_counters.keys()):
    row = []
    row += team.split(',')
    #print(f"{team},", end='')
    for value, count in team_counters[team].items():
        row.append(count)
        #print(f'{count},', end='')
    #print('')
    analysis.append(row)

#print(analysis)

publish_data(analysis, 'NEW Analysis')

