#!/usr/bin/env python3

import math
import calendar
from datetime import datetime, timedelta
import dataset

# Helper date conversion functions
def date_to_datetime(date):
    return(datetime.strptime(date, '%m/%d/%Y'))

def datestamp_to_datetime(datestamp):
    return(datetime.strptime(datetime, '%m/%d%Y %H:%M'))

# League Data

# Week name to date ranges (weeks start on Saturdays)
week_split_data = {
    'Week 1': date_to_datetime('2/28/2020'),
    'Week 2': date_to_datetime('3/7/2020'),
    'Week 3': date_to_datetime('3/14/2020'),
    'Week 4': date_to_datetime('3/21/2020'),
    'Week 5': date_to_datetime('3/28/2020'),
    'Week 6': date_to_datetime('4/4/2020'),
    'Week 7': date_to_datetime('4/11/2020'),
    'Week 8': date_to_datetime('4/18/2020'),
    'Week 9': date_to_datetime('4/25/2020'),
    'Week 10': date_to_datetime('5/2/2020'),
    'Week 11': date_to_datetime('5/9/2020'),
    'Week 12': date_to_datetime('5/16/2020'),
    'Week 13': date_to_datetime('5/23/2020'),
    # Memorial day is Monday 5/25/2020
    'Week 14': date_to_datetime('5/30/2020')
}

division_data = {
    'Lower Farm': {
        'teams': 4,
        'games': 10,
        'playoffs': None
        },
    'Upper Farm': {
        'teams': 6,
        # Dropped from 11 to 10
        'games': 10,
        'playoffs': None
        },
    'Rookie': {
        'teams': 8,
        'games': 13,
        'playoffs': 5
        },
    'Minors AA': {
        'teams': 8,
        'games': 14,
        'playoffs': 5
        },
    'Minors AAA': {
        'teams': 6,
        'games': 14,
        'playoffs': 5
        },
    'Majors': {
        'teams': 10,
        'games': 16,
        'playoffs': 5
        },
    'Softball': {
        'teams': 4,
        'games': 13,
        'playoffs': 5
        },
    'Challenger': {
        'teams': 3,
        'games': 11,
        'playoffs': None,
        'fixed_games': 11
        },
    # JR and SR at Paul Goode - Handled by T.Tullis
    # 'Juniors': {
    #     'teams': 6,
    #     'games': 14,
    #     'playoffs': 5,
    #     'fields': '60-90'
    #     },
    # 'Seniors': {
    #     'teams': 3,
    #     'games': 14,
    #     'playoffs': 2,
    #     'fields': '60-90'
    #     },
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
    'SouthSunset #1 North': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'SouthSunset #2 South': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'Kimbell #1 NW': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'Kimbell #2 SE': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'Paul Goode Practice': {
        'location': 'SF',
        'size': '46/60',
        'type': 'turf',
        'infield': 'turf'
    },
    'Paul Goode Main': {
        'location': 'SF',
        'size': '60/90',
        'type': 'turf',
        'infield': 'turf'
    },        
    'McCoppin': {
        'location': 'SF',
        'size': '60/90',
        'type': 'grass',
        'infield': 'grass'
    },
    'Sweeney': {
        'location': 'SF',
        'size': '60/90',
        'type': 'grass',
        'infield': 'grass'
    },
}


# No games Easter weekend on Saturday or Sunday.
# No games on Memorial Day weekend on Saturday, Sunday or Monday.
blackout_dates = [
    '4/11/2020', '4/12/2020', # Easter (week 11)
    '5/14/2020', # Mothers Day
    '5/23/2020', '5/24/2020', '5/25/2020'  # Memorial Day (week 13)

]
# Datetime conversion for blackouts
blackout_days = [ date_to_datetime(item) for item in blackout_dates ]


# Generate a list of days between start and end
def daterange(start_date, end_date):
    start_date = date_to_datetime(start_date)
    end_date = date_to_datetime(end_date)
    for n in range(int ((end_date - start_date).days) +1 ):
        yield start_date + timedelta(n)

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
                    mydata = dict(
                            week=f"{schedule_week}",
                            week_number=week_number,
                            day_of_week=f"{day_of_week}",
                            date=f"{single_date.date()}",
                            start=f"{start_time}", end=f"{end_time}",
                            datestamp=datestamp,
                            day_of_year=f"{single_date.timetuple().tm_yday}",
                            field=f"{field}",
                            division=None,
                            home_team=None,
                            away_team=None)
                    # adds field data
                    for (key, value) in field_data[field].items():
                        if key is 'field_name': continue  # redundant
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
### Ft. Scott
# Same schedule for North and South
fort_scott=['Ft. Scott - North', 'Ft. Scott - South']
# Sundays  W1-W4
add_time_slots(
    fields=fort_scott,
    days_of_week=['Sunday'],
    start_day='3/1/2020',
    end_day='3/22/2020',
    times=[('11:00','13:15'),('13:15', '15:30')])
# Sundays W5-W8
add_time_slots(
    fields=fort_scott,
    days_of_week=['Sunday'],
    start_day='3/29/2020',
    end_day='4/19/2020',
    times=[('12:30','14:45'),('14:45', '17:00')])

# Sunday W9
add_time_slots(
    fields=fort_scott,
    days_of_week=['Sunday'],
    start_day='4/26/2020',
    end_day='4/26/2020',
    times=[('11:00','13:15'),('13:15', '15:30')])
# Sunday W10 (last usable)
add_time_slots(
    fields=fort_scott,
    days_of_week=['Sunday'],
    start_day='5/3/2020',
    end_day='5/30/2020',
    times=[('09:30','12:30'),('12:30', '15:30')])

# Saturdays W1-W5
add_time_slots(
    fields=fort_scott,
    days_of_week=['Saturday'],
    start_day='3/7/2020',
    end_day='3/28/2020',
    times=[('11:00','13:15'),('13:15', '15:30')])

# Saturdays W6-W14
add_time_slots(
    fields=fort_scott,
    days_of_week=['Saturday'],
    start_day='4/4/2020',
    end_day='5/30/2020',
    times=[('09:30','12:30'),('12:30', '15:30'),('15:30','18:15')])

# Friday W1
add_time_slots(
    fields=fort_scott,
    days_of_week=['Friday'],
    start_day='3/6/2020',
    end_day='5/15/2020',
    times=[('17:00','18:30'),('18:30', '20:30')])

##################
# Tepper and Ketcham
# Saturdays and Sundays
tepper_ketcham = ['Tepper', 'Ketcham']
# Saturday/Sunday
add_time_slots(
    fields=tepper_ketcham,
    days_of_week=['Saturday','Sunday'],
    start_day='2/28/2020',
    end_day='5/31/2020',
    times=[('08:30','11:00'),('11:00', '13:30'),('13:30', '16:00'),('16:00', '18:30')])
# Monday-Friday W2-W4
add_time_slots(
    fields=tepper_ketcham,
    days_of_week=['Monday','Tuesday','Wednesday', 'Thursday', 'Friday'],
    start_day='3/9/2020',
    end_day='3/29/2020',
    times=[('16:30','19:15')])
# Monday-Friday W2-W4
add_time_slots(
    fields=tepper_ketcham,
    days_of_week=['Monday','Tuesday','Wednesday', 'Thursday', 'Friday'],
    start_day='3/30/2020',
    end_day='5/25/2020',
    times=[('17:00','19:30')])

##################
# Sunset
add_time_slots(
    fields=['SouthSunset #1 North'],
    days_of_week=['Friday'],
    start_day='3/6/2020',
    end_day='5/29/2020',
    times=[('17:30','20:00')])

add_time_slots(
    fields=['SouthSunset #2 South'],
    days_of_week=['Tuesday', 'Thursday', 'Friday'],
    start_day='3/3/2020',
    end_day='5/29/2020',
    times=[('17:30','20:00')])

##################
# Kimbell
add_time_slots(
    fields=['Kimbell #1 NW', 'Kimbell #2 SE'],
    days_of_week=['Wednesday'],
    start_day='3/4/2020',
    end_day='5/29/2020',
    times=[('17:30','20:00')])

##################
# Paul Goode
add_time_slots(
    fields=['Paul Goode Practice'],
    days_of_week=['Saturday'],
    start_day='3/13/2020',
    end_day='5/30/2020',
    times=[('11:00','13:00')])

add_time_slots(
    fields=['Paul Goode Practice'],
    days_of_week=['Sunday'],
    start_day='3/8/2020',
    end_day='3/29/2020',
    times=[('13:00','15:00')])

add_time_slots(
    fields=['Paul Goode Practice'],
    days_of_week=['Sunday'],
    start_day='4/5/2020',
    end_day='4/13/2020',
    times=[('12:00','15:00')])

add_time_slots(
    fields=['Paul Goode Practice'],
    days_of_week=['Sunday'],
    start_day='4/19/2020',
    end_day='5/31/2020',
    times=[('1:00','15:00')])


##################
# BIG FIELDS

# # McCoppin (Challenger)
# add_time_slots(
#     fields=['McCoppin'],
#     days_of_week=['Sunday'],
#     start_day='3/8/2020',
#     end_day='5/17/2020',
#     times=[('12:00','15:00')])

# # Sweeney (Juniors)  No May 23
# add_time_slots(
#     fields=['Sweeney'],
#     days_of_week=['Saturday'],
#     start_day='3/7/2020',
#     end_day='5/22/2020',
#     times=[('9:00','12:00')])

# add_time_slots(
#     fields=['Sweeney'],
#     days_of_week=['Saturday'],
#     start_day='5/30/2020',
#     end_day='5/30/2020',
#     times=[('9:00','12:00')])


# Coaches who coach in both divisions -- check for conflicts?
