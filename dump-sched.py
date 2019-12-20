#!/usr/bin/env python3

"""
Script to dump schedule database to a HTML table for easy presentation on a webpage
Uses datatable library for prettier output.
"""

import dataset
import csv

db = dataset.connect('sqlite:///little-league.db')
schedule = db.get_table('schedule')

output = """
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

html = open("docs/output.html", 'w')
html.write(output)

