#!/usr/bin/env python3

import math
import calendar
from datetime import datetime, timedelta
from tracemalloc import start
import dataset
import sys

from string import Template

from season_data import *


class DeltaTemplate(Template):
    delimiter = "%"


# Helper date conversion functions
def date_to_datetime(date):
    return datetime.strptime(date, "%m/%d/%Y")


def datestamp_to_datetime(datestamp):
    return datetime.strptime(datetime, "%m/%d%Y %H:%M")


# Week name to date ranges (weeks start on Saturdays)
week_split_data = {}
start_date = date_to_datetime("9/11/2022")

for week in range(1, 10):
    week_split_data[f"Week {week}"] = start_date + timedelta(7) * (week - 1)

from season_data import division_data, field_data


# No games on Memorial Day weekend on Saturday, Sunday or Monday.
blackout_dates = []
#     '4/11/2020', '4/12/2020', # Easter (week 11)
#     '5/23/2020', '5/24/2020', '5/25/2020'  # Memorial Day (week 13)
# ]
# Datetime conversion for blackouts
blackout_days = [date_to_datetime(item) for item in blackout_dates]


# Generate a list of days between start and end
def daterange(start_date, end_date):
    start_date = date_to_datetime(start_date)
    end_date = date_to_datetime(end_date)
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    hours, rem = divmod(tdelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    d["H"] = "{:02d}".format(hours)
    d["M"] = "{:02d}".format(minutes)
    d["S"] = "{:02d}".format(seconds)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


# Create time slot database
def add_time_slots(
    fields=None,  # One or many fields matching this pattern
    days_of_week=None,  # One or many days valid days of the week
    start_day=None,
    end_day=None,
    times=None,
):

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
                schedule_week = week
                week_number = schedule_week.split(" ")[1]

        # Apply for multilple fields
        for field in fields:
            for (start_time, end_time) in times:
                # print(f"{day_of_week} {single_date.date()} {start_time}-{end_time} {field}")
                (hours, minutes) = start_time.split(":")
                datestamp = single_date + timedelta(
                    hours=int(hours), minutes=int(minutes)
                )

                # # Game start is 30m after field start
                # (start_h, start_m) = start_time.split(":")
                # start_game = timedelta(
                #     hours=int(start_h), minutes=int(start_m)
                # ) + timedelta(minutes=30)

                # start_game_pretty = strfdelta(start_game, "%H:%M")

                # Calculate field time length
                (start_h, start_m) = start_time.split(":")
                (end_h, end_m) = end_time.split(":")
                game_length = (60 * int(end_h) + int(end_m)) - (
                    60 * int(start_h) + int(start_m)
                )
                game_length_pretty = game_length

                mydata = dict(
                    week=f"{schedule_week}",
                    week_number=week_number,
                    day_of_week=f"{day_of_week}",
                    date=f"{single_date.date()}",
                    start=f"{start_time}",
                    end=f"{end_time}",
                    time_length=f"{game_length_pretty}",
                    datestamp=datestamp,
                    day_of_year=f"{single_date.timetuple().tm_yday}",
                    field=f"{field}",
                    division=None,
                    home_team=None,
                    home_team_name=None,
                    away_team=None,
                    away_team_name=None,
                    game_id=None,
                )
                # adds field data
                for (key, value) in field_data[field].items():
                    if key == "field_name":
                        continue  # redundant
                    mydata[key] = value

                table.insert(mydata)


db = dataset.connect("sqlite:///little-league.db")

# Write field data
table = db["fields"]
for (field, data) in field_data.items():
    data["field_name"] = field
    table.insert(data)

# Write team data
table = db["teams"]
for (division, data) in division_data.items():
    data["division_name"] = division
    for teamnumber in range(1, data["teams"] + 1):
        data["team_name"] = f"Team {teamnumber}"
        table.insert(data)

# Write schedule data
table = db["schedule"]

##################
### Ft. Scott
# Same schedule for North and South
fort_scott = ["Ft. Scott - North", "Ft. Scott - South"]

# Sundays  2-slot spots
add_time_slots(
    fields=fort_scott,
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="10/2/2022",
    times=[("08:00", "11:00"), ("11:00", "14:00"), ("14:00", "17:00")],
)
# 10/9 closed for maintenance
add_time_slots(
    fields=fort_scott,
    days_of_week=["Sunday"],
    start_day="10/16/2022",
    end_day="11/6/2022",
    times=[("08:00", "11:00"), ("11:00", "14:00"), ("14:00", "17:00")],
)


# 2h slots for Wall (2,2,2,3) to support TB
add_time_slots(
    fields=["Presidio Wall"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    times=[
        ("09:00", "11:00"),
        ("11:00", "13:00"),
        ("13:00", "15:00"),
        ("15:00", "18:00"),
    ],
)

# mostly 2H slots for Rossi EXCEPT 10/23
add_time_slots(
    fields=["Rossi Park #1"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="10/22/2022",
    times=[
        ("09:00", "11:00"),
        ("11:00", "13:00"),
        ("13:00", "15:00"),
        ("15:00", "18:00"),
    ],
)
# 3h slots on 10/23
add_time_slots(
    fields=["Rossi Park #1"],
    days_of_week=["Sunday"],
    start_day="10/23/2022",
    end_day="10/23/2022",
    times=[
        ("09:00", "12:00"),
        ("12:00", "15:00"),
        ("15:00", "18:00"),
    ],
)
add_time_slots(
    fields=["Rossi Park #1"],
    days_of_week=["Sunday"],
    start_day="10/24/2022",
    end_day="11/6/2022",
    times=[
        ("09:00", "11:00"),
        ("11:00", "13:00"),
        ("13:00", "15:00"),
        ("15:00", "18:00"),
    ],
)

add_time_slots(
    fields=["Visitation Valley"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    times=[("09:00", "12:00"), ("12:00", "15:00"), ("15:00", "18:00")],
)

add_time_slots(
    fields=["West Sunset #1", "Balboa Sweeney", "Sunset Rec"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    times=[("09:00", "12:00"), ("12:00", "15:00"), ("15:00", "18:00")],
)

# Laurel is mostly 3h slots except 10/23
add_time_slots(
    fields=[
        "Laurel Hill",
    ],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="10/22/2022",
    times=[("09:00", "12:00"), ("12:00", "15:00"), ("15:00", "18:00")],
)
# 2h slots on 10/23
add_time_slots(
    fields=[
        "Laurel Hill",
    ],
    days_of_week=["Sunday"],
    start_day="10/23/2022",
    end_day="10/23/2022",
    times=[
        ("09:00", "11:00"),
        ("11:00", "13:00"),
        ("13:00", "15:00"),
        ("15:00", "18:00"),
    ],
)
add_time_slots(
    fields=[
        "Laurel Hill",
    ],
    days_of_week=["Sunday"],
    start_day="10/24/2022",
    end_day="11/6/2022",
    times=[("09:00", "12:00"), ("12:00", "15:00"), ("15:00", "18:00")],
)


add_time_slots(
    fields=["West Sunset #3"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    times=[("12:00", "15:00"), ("15:00", "18:00")],
)

add_time_slots(
    fields=["Paul Goode Main", "Paul Goode Practice"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    times=[("12:00", "15:00")],
)

add_time_slots(
    fields=["Tepper", "Ketcham"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    times=[("08:30", "11:30"), ("11:30", "14:30"), ("14:30", "17:30")],
)

add_time_slots(
    fields=["Parkside"],
    days_of_week=["Sunday"],
    start_day="9/11/2022",
    end_day="11/6/2022",
    # last slot isn't 3H
    times=[("09:00", "12:00"), ("12:00", "15:00")],
)
add_time_slots(
    fields=["Balboa D2"],
    days_of_week=["Sunday"],
    start_day="10/9/2022",
    end_day="10/9/2022",
    # last slot isn't 3H
    times=[("09:00", "12:00"), ("12:00", "15:00"), ("15:00", "18:00")],
)
add_time_slots(
    fields=["Crocker D3"],
    days_of_week=["Sunday"],
    start_day="10/9/2022",
    end_day="10/9/2022",
    # last slot isn't 3H
    times=[
        ("09:00", "12:00"),
        ("12:00", "15:00"),
    ],
)

add_time_slots(
    fields=["Palega"],
    days_of_week=["Sunday"],
    start_day="10/9/2022",
    end_day="10/9/2022",
    # last slot isn't 3H
    times=[
        ("09:00", "12:00"),
    ],
)


sys.exit()
