#!/usr/bin/env python3

import dataset
from datetime import datetime, timedelta
from itertools import combinations
import faceoffs
import math
import random
import sys
random.seed(2020)

# Data
db = dataset.connect('sqlite:///little-league.db')

teams = db.get_table('teams')
fields = db.get_table('fields')
schedule = db.get_table('schedule')

# helpers
fort_scott=['Ft. Scott - North', 'Ft. Scott - South']
farm_scott_goode=['Ft. Scott - South', 'Paul Goode Practice']
tepper_ketcham = ['Tepper', 'Ketcham']
weekdays=['Monday','Tuesday','Wednesday', 'Thursday', 'Friday']
monday_thursday=['Monday','Tuesday','Wednesday', 'Thursday']
anyday_but_friday=['Monday','Tuesday','Wednesday', 'Thursday', 'Saturday', 'Sunday']
fields_4660_sf  = [ i['field_name'] for i in fields.find(size='46/60', location='SF')]
fields_4660_all  = [ i['field_name'] for i in fields.find(size='46/60')]


##########################################################################################
### Reservations
# 1. RESERVE both Ft. Scotts for Lower Farm Fridays from 5-6:30pm
for slot in schedule.find(day_of_week='Friday', start='17:00', field=fort_scott):
    print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto Lower Farm")
    data = dict(id=slot['id'], home_team='RESERVED - Practice', division='Lower Farm')
    schedule.update(data, ['id'])

# 2. RESERVE Tepper for Challengers on Sundays 3/7-5/31 from 13:30
for slot in schedule.find(day_of_week='Sunday', start='13:30', field=['Tepper']):
    if slot['datestamp'] < datetime(2020,3,7) or slot['datestamp'] > datetime(2020,6,1):
        continue
    print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto Challengers")
    data = dict(id=slot['id'], home_team='RESERVED', division='Challengers')
    schedule.update(data, ['id'])

# 3. RESERVE a slot for Softball on Week 1 on TI.
for slot in schedule.find(week='Week 1',  infield='dirt', field=tepper_ketcham, _limit=1):
    print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto Softball")
    data = dict(id=slot['id'], home_team='RESERVED', division='Softball')
    schedule.update(data, ['id'])

# 4. RESERVE one game per week at Ft. Scott South on Sunday afternoon.  No other games.
for week in range(2,11):
    for slot in schedule.find(day_of_week='Sunday', 
                week_number=week, infield='dirt', field=fort_scott,
                order_by=['-datestamp'], _limit=1):
        print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto Softball")
        data = dict(id=slot['id'], home_team='RESERVED', division='Softball')
        schedule.update(data, ['id'])

##########################################################################################
stuck_todo={}

def stuck(division=None, todo=None):
    remain = len(list(schedule.find(home_team=None)))
    remain_weekday_sf=len(list(schedule.find(home_team=None,
                    day_of_week=monday_thursday, fields=fields_4660_sf)))
    remain_sf=len(list(schedule.find(home_team=None,
                    fields=fields_4660_sf)))

    print('='*80)
    print('STUCK')
    print(f"Remaining Slots: {remain}")
    print(f"Remaining SF Weekday Slots: {remain_weekday_sf}")
    print(f"Remaining SF Slots: {remain_sf}")
    stuck_todo[division]=todo
    print('STUCK:', stuck_todo)
    #exit(1)


def get_team_list(division):
    return([ team['team_name'] for team in teams.distinct('team_name', division_name=division)])

def get_total_games(division):
    division_data=teams.find_one(division_name=division)
    games_per_team = division_data['games']

    team_list = get_team_list(division)

    total_games = games_per_team * len(team_list) // 2
    return(total_games)

def get_faceoffs(division):
    team_list = get_team_list(division)
    total_games = get_total_games(division)

    faceoff_list = faceoffs.faceoffs_repeated(team_list, total_games)
    print('='*80)
    print(f"Division: {division}\n\tTeams: {len(team_list)}\n\tTotal Games: {total_games}")

    return(faceoff_list)

def weekly_minimum(division, week=None, weeks=None):
    team_list = get_team_list(division)
    min_games = len(team_list) // 2

    total_games = get_total_games(division)

    if total_games/weeks > min_games:
        print(f'WARN: Need {total_games} total games and only have have {weeks} weeks.')
        min_games = int(total_games/weeks)

    return(min_games)

def schedule_by_week(division=None,
                    start_week=None, end_week=None,
                    day_of_week_prefs=None,
                    field_prefs=None,
                    faceoff_list=None,
                    weekend_percent=None):


    working_faceoffs = get_faceoffs(division=division)

    weeks = end_week - start_week
    weekly_min = weekly_minimum(division, weeks=weeks)
    weekly_faceoffs = []

    for week in range(start_week, end_week + 1):


        print('-'*80)
        print(f"Week {week} - trying find {weekly_min} spots for {division}")

        # Get new weekly assignments if we don't have them
        if len(weekly_faceoffs) < weekly_min:
            needed = weekly_min - len(weekly_faceoffs)

            weekly_faceoffs = weekly_faceoffs + working_faceoffs[:needed]
            # shrink total working list
            working_faceoffs = working_faceoffs[needed:]

        for day_of_week in day_of_week_prefs:
            for fields in field_prefs:
                if len(weekly_faceoffs) > 0:
                    weekly_faceoffs = complex_assign(division=division,
                                                day_of_week=day_of_week,
                                                start_week=week, end_week=week,
                                                fields=fields,
                                                faceoff_list=weekly_faceoffs)
        placed = weekly_min - len(weekly_faceoffs)
        print(f'Found: {placed}   Total Games Left: {len(working_faceoffs) + len(weekly_faceoffs)}')
    if len(working_faceoffs) > 0: stuck(division=division, todo=working_faceoffs)

def complex_assign(division=None, 
                    start_week=None, end_week=None, 
                    day_of_week=None, fields=None, 
                    max_per_week=None, faceoff_list=None, 
                    max_per_week_pattern=None,
                    weekend_percent=None):

    print(f"  Checking for slots on {day_of_week} at {fields}")

    for week in range(start_week,end_week+1):
        matching_slots=list(schedule.find(
                                day_of_week=day_of_week,
                                week_number=week,
                                field=fields))

        # Shuffle the usable slots (more fair results)
        random.shuffle(matching_slots)

        for slot in matching_slots:
            if slot['home_team'] is not None: 
                continue  # already booked

            if slot['location'] == "TI" and slot['day_of_week'] == 'Friday': 
                continue # Skip Fridays at TI

            if len(faceoff_list) == 0:
                continue # No more work to be done

            # Back to back checking (refactor?)
            back_to_back = False

            day_of_year = int(slot['day_of_year'])
            prior_day_slots = list(schedule.find(day_of_year=str(day_of_year-1), division=division))
            next_day_slots  = list(schedule.find(day_of_year=str(day_of_year+1), division=division))

            (home_team, away_team) = faceoff_list[:1][0]
            for checkslot in prior_day_slots:
                if home_team == checkslot['home_team'] or home_team == checkslot['away_team']:
                    back_to_back = True
            for checkslot in next_day_slots:
                if away_team == checkslot['home_team'] or away_team == checkslot['away_team']:
                    back_to_back = True
            if back_to_back:
                # Cannot schedule this game in this slot...
                continue

            try:
                (home_team, away_team)=faceoff_list.pop(0)
            except :
                # No games left to assign
                continue

            print(f"    ✅ Assigned {slot['day_of_week']: <10} {slot['datestamp']} @ {slot['field']: <20} to {division: <15} - {home_team: <7} vs {away_team: <7}")
            data = dict(id=slot['id'], home_team=home_team,
                    away_team=away_team, division=division)
            schedule.update(data, ['id'])

    return(faceoff_list)

##########################################################################################
### Main schedule:

# Lower Farm and Upper Farm have only weekend games and ends on 5/17.
# have Upper Farm games on Saturday and Lower Farm games all on Sunday
schedule_by_week(division='Lower Farm', 
                start_week=2, end_week=12,
                day_of_week_prefs=[['Sunday']],
                field_prefs=[['Ft. Scott - South', 'Paul Goode Practice']]
                )

schedule_by_week(division='Upper Farm', 
                start_week=2, end_week=12,
                day_of_week_prefs=[['Saturday']],
                field_prefs=[['Ft. Scott - South', 'Paul Goode Practice'], ['Ft. Scott - North']]
                )

# 6. Rookie is supposed to end on May 5/17 but also have playoffs.
# We should probably plan on pool play with two pools of 4 teams, and the  winner from each pool playing
# a championship game on 5/17 at Tepper.  That means likely starting playoffs on or about May 4 with three
# pool play games each.  That keeps more teams playing longer.
# The following weekend is Memorial Day, so it would be good to get done before that.
# No mid-week games on TI for AA or Rookie.

schedule_by_week(division='Rookie', 
                start_week=2, end_week=12,
                day_of_week_prefs=[['Saturday','Sunday'],['Wednesday']],
                field_prefs=[['Ft. Scott - South', 'Paul Goode Practice'], ['Ft. Scott - North'], fields_4660_sf]
                )


# Minors AA
# AA playoffs beginning on or about May 11 (week 11?)
# No mid-week games on TI for AA
schedule_by_week(division='Minors AA', 
                start_week=2, end_week=11,
                day_of_week_prefs=[['Saturday','Sunday'], weekdays],
                field_prefs=[['Ft. Scott - North'], fields_4660_sf, fields_4660_all]
                )


# Minors AAA
# AAA  playoffs beginning as late as May 16.

schedule_by_week(division='Minors AAA', 
                start_week=2, end_week=11,
                day_of_week_prefs=[['Saturday','Sunday'], weekdays],
                field_prefs=[['Ft. Scott - North'], fields_4660_sf, fields_4660_all]
                )

# Majors
# Majors should start on the weekend of 2/29 and 3/1 on TI.
# we should have all 10 Majors teams have a TI game scheduled for that weekend.
# Majors playoffs beginning on May 9.


schedule_by_week(division='Majors', 
                start_week=2, end_week=11,
                day_of_week_prefs=[['Saturday','Sunday'], weekdays],
                field_prefs=[['Ft. Scott - North'], fields_4660_sf, fields_4660_all]
                )



"""

3. No Friday games on TI unless absolutely necessary.

7. PLAYOFFS
Majors playoffs beginning on May 9.
Pool play seems likely for all to keep kids playing longer.
AA, AAA and Majors finals all at Tepper on the weekend of May 30-31.

8.  Minors softball –
one game per week at Ft. Scott South on Sunday afternoon.  No other games.

9. Mid-week TI games for Majors should max out at 5 per team.

10.Mid-week TI games for Minors AAA should max out at 3 per team.


Nice to haves

3.            We knew that games beginning at 6:30 at Ft. Scott could realistically only be Majors (and maybe…. Just maybe…. 
Minors which was then a combination of AAA and AA).  Ft. Scott South is not great for Majors given the funky mound there, so that could leave an empty field space on Friday evening.

4.            We knew really only Majors and more rarely AAA would use TI on a weekday and even then we wanted to spread those out evenly.  We wanted to max Majors out at 5 to 6 mid-week game on TI (knowing that some would rain out) and Minors (i.e. AAA/AA) at 2 to 3 mid-week games out there.


1.  15U Softball schedule is unknown right now.  
Will likely need space on some weekends at Ketcham or Ft. Scott South.  
Should likely reserve some space there for 15U Softball that might be filled in later by others

2.  All Rookie, AA and AAA teams should have the opportunity 
to play one weekend game at Tepper, preferably not the first 
or last game (there are extra parent duties for those games).

3.  For teams playing multiple games on TI, there should 
be a relatively even mix between Tepper and Ketcham.

4.  Depending on our turf allocation from Rec & Park,
we should spread those games out as evenly as possible, 
particularly in the early season when rain is more likely.

5.  We should try to achieve balance between teams such 
that if teams play multiple times against each other 
there is some time between such meetings.

 """

