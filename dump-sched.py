#!/usr/bin/env python3

import dataset
import csv

db = dataset.connect('sqlite:///little-league.db')
schedule = db.get_table('schedule')

import csv
with open('schedule.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter='|')
    for slot in schedule.all(order_by=['datestamp']):
        print(slot.values())
        writer.writerow(slot.values())
