#!/usr/bin/env python3

import dataset
import csv

db = dataset.connect('sqlite:///little-league.db')
schedule = db.get_table('schedule')

import csv

print('|', end='')
for header in schedule.find_one().keys():
    print(f"{header}|", end='')
print()

print('|', end='')
for header in schedule.find_one().keys():
    print(f" --- |", end='')
print()




for slot in schedule.all(order_by=['datestamp']):
    print('|', end='')
    for column in slot.values():
        print(f"{column}|", end='')
    print()

