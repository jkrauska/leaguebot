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

for slot in schedule.all():
    if slot['home_team'] is not None and slot['division'] is not None:
        field_types['%s - %s - %s' % (slot['division'], slot['home_team'], slot['type'])] += 1
        field_types['%s - %s - %s' % (slot['division'], slot['away_team'], slot['type'])] += 1


for value, count in sorted(field_types):
    print(value, count)