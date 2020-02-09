#!/usr/bin/env python3

"""
Script to dump schedule database to a HTML table for easy presentation on a webpage
Uses datatable library for prettier output.
"""

import dataset
import datafreeze
import csv
from collections import Counter, defaultdict

db = dataset.connect('sqlite:///little-league.db')

teams = db.get_table('teams')
fields = db.get_table('fields')
schedule = db.get_table('schedule')


team_counters=defaultdict()

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
            #print(division_and_team)

            if division_and_team not in team_counters:
                team_counters[division_and_team] = Counter()

            team_counters[division_and_team]['total'] += 1

            team_counters[division_and_team][slot['type']] += 1
            team_counters[division_and_team][slot['location']] += 1
            team_counters[division_and_team][slot['day_of_week']] += 1
            team_counters[division_and_team][f"{slot['day_of_week']}-{slot['location']}" ] += 1


for team in team_counters:
    print('REPORT', team, '-', end='')
    for value, count in team_counters[team].items():
        print(f' {value}={count},', end='')
    print('')
