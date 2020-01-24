#!/usr/bin/env python3

import dataset
from datetime import datetime, timedelta
from itertools import combinations
import faceoffs
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
tepper_ketcham = ['Tepper', 'Ketcham']
weekdays=['Monday','Tuesday','Wednesday', 'Thursday', 'Friday']
monday_thursday=['Monday','Tuesday','Wednesday', 'Thursday']
anyday_but_friday=['Monday','Tuesday','Wednesday', 'Thursday', 'Saturday', 'Sunday']
fields_4660_sf  = [ i['field_name'] for i in fields.find(size='46/60', location='SF')]
fields_4660_all  = [ i['field_name'] for i in fields.find(size='46/60')]


##########################################################################################
### Reservations
# 1. RESERVE both Ft. Scotts for Lower Farm Fridays from 5-6:30pm
asignee='RESERVED Lower Farm Practice'
for slot in schedule.find(day_of_week='Friday', start='17:00', field=fort_scott):
    print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto {asignee}")
    data = dict(id=slot['id'], home_team=asignee)
    schedule.update(data, ['id'])

# 2. RESERVE Tepper for Challengers on Sundays 3/7-5/31 from 13:30
asignee='RESERVED Challengers'
for slot in schedule.find(day_of_week='Sunday', start='13:30', field=['Tepper']):
    if slot['datestamp'] < datetime(2020,3,7) or slot['datestamp'] > datetime(2020,6,1):
        continue
    print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto {asignee}")
    data = dict(id=slot['id'], home_team=asignee)
    schedule.update(data, ['id'])

# 3. RESERVE a slot for Softball on Week 1 on TI.
asignee='RESERVED Softball'
for slot in schedule.find(week='Week 1',  infield='dirt', field=tepper_ketcham, _limit=1):
    print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto {asignee}")
    data = dict(id=slot['id'], home_team=asignee)
    schedule.update(data, ['id'])

# 4. RESERVE one game per week at Ft. Scott South on Sunday afternoon.  No other games.
asignee='RESERVED Softball'
for week in range(2,11):
    for slot in schedule.find(day_of_week='Sunday', 
                week_number=week, infield='dirt', field=fort_scott,
                order_by=['-datestamp'], _limit=1):
        print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto {asignee}")
        data = dict(id=slot['id'], home_team=asignee)
        schedule.update(data, ['id'])

##########################################################################################

def stuck():
    remain = len(list(schedule.find(home_team=None)))
    remain_weekday_sf=len(list(schedule.find(home_team=None,
                    day_of_week=monday_thursday, fields=fields_4660_sf)))
    remain_sf=len(list(schedule.find(home_team=None,
                    fields=fields_4660_sf)))

    print('='*80)
    print(f"Remaining Slots: {remain}")
    print(f"Remaining SF Weekday Slots: {remain_weekday_sf}")
    print(f"Remaining SF Slots: {remain_sf}")

    exit("STUCK")


def complex_assign(division=None, 
                    start_week=2, end_week=12, 
                    day_of_week=None, fields=None, 
                    max_per_week=None, faceoff_list=None):
    print('='*80)
    print(f"Running Assignments for Division: {division}")

    team_list = [ team['team_name'] for team in teams.distinct('team_name', division_name=division)]
    division_data=teams.find_one(division_name=division)
    games=division_data['games']
    total_games = games * len(team_list) // 2


    # Generate faceoffs if not given.
    if faceoff_list is None:
        faceoff_list = faceoffs.faceoffs_repeated(team_list, total_games)


        print(f"Teams: {len(team_list)}\nGames Per Team: {games}\nTotal Games: {total_games}")
    else:
        print(f"Running remaining {len(faceoff_list)} placements")

    if max_per_week is None:
        max_per_week=len(team_list) // 2

    scheduled=0

    for week in range(start_week,end_week+1):
        week_count=0

        print('-'*80)
        matching_slots=list(schedule.find(
                    day_of_week=day_of_week,
                    week_number=week,
                    field=fields))

        # Shuffle the usable slots (more fair results)
        random.shuffle(matching_slots)

        for slot in matching_slots:
            if week_count >= max_per_week: continue  # total for week met
            if slot['home_team'] is not None: continue  # already booked

            if slot['location'] == "TI" and slot['day_of_week'] == 'Friday': 
                continue # Skip Fridays at TI

            try:
                (home_team, away_team)=faceoff_list.pop(0)
            except :
                # No games left to assign
                continue

            print(f"Week: {week}, Assigned {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto {division} \t- {home_team} vs {away_team} to Slot {slot['id']}, Left to do: {len(faceoff_list)}")
            data = dict(id=slot['id'], home_team=home_team,
                    away_team=away_team, division=division)
            schedule.update(data, ['id'])
            week_count+=1
            scheduled+=1
    print('-'*80)
    print('-'*80)
    print(f"Remaining Game Count: {len(faceoff_list)}")


    remain = len(list(schedule.find(home_team=None)))
    print(f"Remaining Schedule Slots: {remain}")
    return(faceoff_list)

##########################################################################################
### Main schedule:

# Lower Farm and Upper Farm have only weekend games and ends on 5/17.
# have Upper Farm games on Saturday and Lower Farm games all on Sunday
 
remain = complex_assign(division='Lower Farm', start_week=2, end_week=12, day_of_week='Sunday',   fields=fort_scott)
if len(remain) > 0: sys.exit('STUCK')


remain = complex_assign(division='Upper Farm', start_week=2, end_week=12, day_of_week='Saturday', fields=fort_scott)
remain = complex_assign(division='Upper Farm', 
                            faceoff_list=remain,
                            start_week=9, end_week=12,
                            max_per_week=1,
                            day_of_week=monday_thursday, fields=fields_4660_sf)

if len(remain) > 0: stuck()


# 6. Rookie is supposed to end on May 5/17 but also have playoffs.
# We should probably plan on pool play with two pools of 4 teams, and the  winner from each pool playing
# a championship game on 5/17 at Tepper.  That means likely starting playoffs on or about May 4 with three
# pool play games each.  That keeps more teams playing longer.
# The following weekend is Memorial Day, so it would be good to get done before that.
# No mid-week games on TI for AA or Rookie.
remain = complex_assign(division='Rookie', start_week=2, end_week=12, 
                day_of_week=['Saturday', 'Sunday'], fields=fields_4660_sf)

remain = complex_assign(division='Rookie', start_week=5, end_week=12,
                faceoff_list=remain,
                max_per_week=3,
                day_of_week=monday_thursday, fields=fields_4660_sf)
if len(remain) > 0: stuck()


# Minors AA
# AA playoffs beginning on or about May 11 (week 11?)
# No mid-week games on TI for AA
remain = complex_assign(division='Minors AA', start_week=2, end_week=11, 
                day_of_week=['Saturday', 'Sunday'], fields=fields_4660_all)

# Schedule remaining M-Thurs to avoid Friday/Sautday Mix
remain = complex_assign(division='Minors AA', start_week=2, end_week=11,
                faceoff_list=remain,
                max_per_week=3,
                day_of_week=weekdays, fields=fields_4660_sf)
if len(remain) > 0: stuck()


# Minors AAA
# AAA  playoffs beginning as late as May 16.
remain = complex_assign(division='Minors AAA', start_week=2, end_week=11, 
                day_of_week=['Saturday', 'Sunday'], fields=fields_4660_all)

remain = complex_assign(division='Minors AAA', start_week=2, end_week=11,
                max_per_week=2,
                faceoff_list=remain,
                day_of_week=weekdays, fields=fields_4660_all)
if len(remain) > 0: stuck()

# Majors
# Majors should start on the weekend of 2/29 and 3/1 on TI.
# we should have all 10 Majors teams have a TI game scheduled for that weekend.
# Majors playoffs beginning on May 9.
remain = complex_assign(division='Majors', start_week=2, end_week=10, 
                day_of_week=['Saturday', 'Sunday'], fields=fields_4660_all)

remain = complex_assign(division='Majors', start_week=2, end_week=10,
                max_per_week=4,
                faceoff_list=remain,
                day_of_week=weekdays, fields=fields_4660_all)
if len(remain) > 0: stuck()


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

3.            We knew that games beginning at 6:30 at Ft. Scott could realistically only be Majors (and maybe…. Just maybe…. Minors which was then a combination of AAA and AA).  Ft. Scott South is not great for Majors given the funky mound there, so that could leave an empty field space on Friday evening.

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

