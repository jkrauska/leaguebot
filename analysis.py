#!/usr/bin/env python3

"""
Script to dump schedule database to a HTML table for easy presentation on a webpage
Uses datatable library for prettier output.
"""

import dataset
import datafreeze
import csv
from collections import Counter

db = dataset.connect('sqlite:///little-league.db')

teams = db.get_table('teams')
fields = db.get_table('fields')
schedule = db.get_table('schedule')

field_types=Counter()

"""
- Analysis pass per team
turf vs grass
ti vs sf
weekend vs weekday
home vs away
field count
"""

for slot in schedule.all():
    for team in [slot['home_team'], slot['away_team']]:
        if team is not None:
            division_and_team = '%s - %s' % (slot['division'], team)
            field_types['%s - %s' % (division_and_team, slot['type'])] += 1


print(field_types)
for value, count in sorted(field_types):
    print(value, count)