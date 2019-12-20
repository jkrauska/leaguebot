#!/usr/bin/env python3

import dataset
import csv

db = dataset.connect('sqlite:///little-league.db')
schedule = db.get_table('schedule')

# import csv

# print('|', end='')
# for header in schedule.find_one().keys():
#     print(f"{header}|", end='')
# print()

# print('|', end='')
# for header in schedule.find_one().keys():
#     print(f" --- |", end='')
# print()

# for slot in schedule.all(order_by=['datestamp']):
#     print('|', end='')
#     for column in slot.values():
#         print(f"{column}|", end='')
#     print()

output = "<html>"
output +="<head>"
output+="""<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.20/css/jquery.dataTables.css">"""
output +="</head>"
output +="<body>"




output += """
<table id="table_id" class="display">
<thread>
<tr>"""


for header in schedule.find_one().keys():
    output += f"<th>{header}</th>"
output += '</tr></thread>'

output += "<tr>"
for slot in schedule.all(order_by=['datestamp']):
    for column in slot.values():
        output+=f"<td>{column}</td>"
    output+='</tr>'

output+="""</table>
<script
  src="https://code.jquery.com/jquery-3.4.1.slim.min.js"
  integrity="sha256-pasqAKBDmFT4eHoN2ndd6lN370kFiGUFyTiUHWhU7k8="
  crossorigin="anonymous"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.20/js/jquery.dataTables.js"></script>

  <script>
  $(function(){
    $("#table_id").dataTable();
  })
  </script>
</body>
</html>
"""

hs = open("docs/output.html", 'w')
hs.write(output)

