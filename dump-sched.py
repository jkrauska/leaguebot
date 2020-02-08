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
schedule = db.get_table('schedule')


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



# Google Sheet
sa = SpreadsheetApp('secret.json')
spreadsheet = sa.open_by_id('12BDEIWO_85BN6egolnUqIpHQ6yRPyx35VnccSCQD2Ag')
try:
    spreadsheet.create_sheets('NEW')
except:
    pass

sheet = spreadsheet.get_sheet_by_name('NEW')


output = []
header = list(schedule.find_one().keys())
output.append(header)
for slot in schedule.all(order_by=['datestamp']):
    output.append(list(slot.values()))

data_range = sheet.get_range(row=1, 
                            column=1, 
                            number_of_row=len(output),
                            number_of_column=(len(output[0])))

# Apply
data_range.set_values(output)