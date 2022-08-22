#!/usr/bin/env python3

import math
import calendar
from datetime import datetime, timedelta
import dataset
import sys

from string import Template

class DeltaTemplate(Template):
    delimiter = "%"

# Helper date conversion functions
def date_to_datetime(date):
    return(datetime.strptime(date, '%m/%d/%Y'))

def datestamp_to_datetime(datestamp):
    return(datetime.strptime(datetime, '%m/%d%Y %H:%M'))

# League Data

# Week name to date ranges (Sundays only)
first_day=date_to_datetime('9/12/2021')

week_split_data = {}
for x in range(0,9):
    week_split_data[f"Week {x+1}"] = first_day + timedelta(days=x*7)



division_data = {
    'Farm - Lower': {
        'teams': 6,
        'games': 9,
        'playoffs': None
        },
    'Farm - Upper': {
        'teams': 6,
        'games': 9,
        'playoffs': None
        },
    'Rookie': {
        'teams': 6,
        'games': 9,
        'playoffs': 5
        },
    'Minors AA': {
        'teams': 8,
        'games': 7,
        'playoffs': 2
        },
    'Minors AAA': {
        'teams': 8,
        'games': 7,
        'playoffs': 2
        },
    'Majors': {
        'teams': 10,
        'games': 7,
        'playoffs': 2
        },
    'Softball': {
        'teams': 2,
        'games': 9,
        'playoffs': 0
        },
    # 'Challenger': {
    #     'teams': 3,
    #     'games': 11,
    #     'playoffs': None,
    #     'fixed_games': 11
    #     },
    # JR and SR at Paul Goode - Handled by T.Tullis
    'Juniors': {
        'teams': 8,
        'games': 7,
        'playoffs': 2,
        'fields': '60-90'
        },
    'Seniors': {
        'teams': 4,
        'games': 7,
        'playoffs': 2,
        'fields': '60-90'
        },
}

field_data = {
    'Ft. Scott - North': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Ft. Scott - South': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'dirt'
    },
    'Tepper': {
        'location': 'TI',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Ketcham': {
        'location': 'TI',
        'size': '46/60',
        'type': 'grass',
        'infield': 'dirt'
    },
    'Paul Goode Practice': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'Paul Goode Main': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'Julias Kahn along Presidio Wall': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Balboa Park #1 - Near Skatepark': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Balboa Park #2 - Near Playground': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Rossi Park #1': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },

    'West Sunset #3': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'West Sunset #2': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'West Sunset #1': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Big Rec Sunberg': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },
    'Big Rec Nealon': {
        'location': 'SF',
        'size': '46/60',
        'type': 'grass',
        'infield': 'grass'
    },

}


# No games Easter weekend on Saturday or Sunday.
# No games on Memorial Day weekend on Saturday, Sunday or Monday.
blackout_dates = []
#     '4/11/2020', '4/12/2020', # Easter (week 11)
#     '5/23/2020', '5/24/2020', '5/25/2020'  # Memorial Day (week 13)
# ]
# Datetime conversion for blackouts
blackout_days = [ date_to_datetime(item) for item in blackout_dates ]


# Generate a list of days between start and end
def daterange(start_date, end_date):
    start_date = date_to_datetime(start_date)
    end_date = date_to_datetime(end_date)
    for n in range(int ((end_date - start_date).days) +1 ):
        yield start_date + timedelta(n)


def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = '{:02d}'.format(hours)
    d["M"] = '{:02d}'.format(minutes)
    d["S"] = '{:02d}'.format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)

# Create time slot database
def add_time_slots(
    fields=None, # One or many fields matching this pattern
    days_of_week=None, # One or many days valid days of the week
    start_day=None, end_day=None,
    times=None):

        for single_date in daterange(start_day, end_day):
            day_of_week = calendar.day_name[single_date.weekday()]

            # Skip conditions
            if day_of_week not in days_of_week:
                continue
            if single_date in blackout_days:
                continue

            # Determine week number
            for (week, week_start) in week_split_data.items():
                if single_date >= week_start:
                    schedule_week=week
                    week_number=schedule_week.split(' ')[1]

            # Apply for multikple fields
            for field in fields:
                for (start_time, end_time) in times:
                    #print(f"{day_of_week} {single_date.date()} {start_time}-{end_time} {field}")
                    (hours, minutes) = start_time.split(':')
                    datestamp = single_date + timedelta(hours=int(hours), minutes=int(minutes))

                    # Game start is 30m after field start
                    (start_h, start_m) = start_time.split(':')
                    start_game = timedelta(hours=int(start_h), minutes=int(start_m)) + timedelta(minutes=30)
                    start_game_pretty = strfdelta(start_game, '%H:%M')

                    # Calculate game length
                    (end_h, end_m) = end_time.split(':')
                    game_length = timedelta(hours=int(end_h), minutes=int(end_m)) - start_game
                    game_length_pretty = strfdelta(game_length, '%H:%M')

                    mydata = dict(
                            week=f"{schedule_week}",
                            week_number=week_number,
                            day_of_week=f"{day_of_week}",
                            date=f"{single_date.date()}",
                            start=f"{start_time}", 
                            start_game=f"{start_game_pretty}",
                            end=f"{end_time}",
                            game_length=f"{game_length_pretty}",
                            datestamp=datestamp,
                            day_of_year=f"{single_date.timetuple().tm_yday}",
                            field=f"{field}",
                            division=None,
                            home_team=None,
                            away_team=None,
                            game_id=None)
                    # adds field data
                    for (key, value) in field_data[field].items():
                        if key == 'field_name': continue  # redundant
                        mydata[key] = value

                    table.insert(mydata)

db = dataset.connect('sqlite:///little-league.db')

# Write field data
table = db['fields']
for (field, data) in field_data.items():
    data['field_name'] = field
    table.insert(data)

# Write team data
table = db['teams']
for (division, data) in division_data.items():
    data['division_name'] = division


    for teamnumber in range(1, data['teams']+1):
        data['team_name'] = f"Team {teamnumber}"
        table.insert(data)

# Write schedule data
table = db['schedule']

##################
# Paul Goode 2 hour slots
add_time_slots(
    fields=['Paul Goode Practice'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('09:00','11:00'),('11:00', '13:00'),('13:00', '15:00')])


# Paul Goode 2 hour slots
add_time_slots(
    fields=['Paul Goode Main'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('14:00','17:00')])

# JK - 3 hour slots
add_time_slots(
    fields=['Julias Kahn along Presidio Wall'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('09:00','12:00'),('12:00', '15:00'),('15:00', '18:00')])


add_time_slots(
    fields=['Balboa Park #1 - Near Skatepark','Balboa Park #2 - Near Playground','Rossi Park #1'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('09:00','12:00'),('12:00', '15:00'),('15:00', '18:00')])

add_time_slots(
    fields=['Ketcham', 'Tepper'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('09:00','12:00'),('12:00', '15:00'),('15:00', '18:00')])

add_time_slots(
    fields=['West Sunset #3', 'West Sunset #1'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('09:00','12:00'),('12:00', '15:00')])


add_time_slots(
    fields=['West Sunset #2'],
    days_of_week=['Sunday'],
    start_day='9/12/2021',
    end_day='11/7/2021',
    times=[('09:00','12:00'),('12:00', '15:00'),('15:00', '18:00')])


