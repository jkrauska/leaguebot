#!/usr/bin/env python3

import dataset
from datetime import datetime, timedelta
from itertools import combinations


# helpers
fort_scott=['Ft. Scott - North', 'Ft. Scott - South']
tepper_ketcham = ['Tepper', 'Ketcham']


db = dataset.connect('sqlite:///little-league.db')

teams = db.get_table('teams')
fields = db.get_table('fields')
schedule = db.get_table('schedule')

# Run rules

### Reservations
# 1. RESERVE both Ft. Scotts for Lower Farm Fridays from 5-6:30pm
for slot in schedule.find(day_of_week='Friday', start='17:00', field=fort_scott):
    data = dict(id=slot['id'], home_team='RESERVED Lower Farm Practice')
    schedule.update(data, ['id'])

# 2. RESERVE Tepper for Challengers on Sundays 3/7-5/31 from 13:30
for slot in schedule.find(day_of_week='Sunday', start='13:30', field=['Tepper']):
    if slot['datestamp'] < datetime(2020,3,7) or slot['datestamp'] > datetime(2020,6,1):
        continue
    data = dict(id=slot['id'], home_team='RESERVED Challengers')
    schedule.update(data, ['id'])

# 3. RESERVE a slot for Softball on Week 1 on TI.
for slot in schedule.find(week='Week 1',  infield='dirt', field=tepper_ketcham, _limit=1):
    data = dict(id=slot['id'], home_team='RESERVED Softball')
    schedule.update(data, ['id'])


### Main schedule:


# Lower Farm and Upper Farm have only weekend games and ends on 5/17.
# have Upper Farm games on Saturday and Lower Farm games all on Sunday
# Need  Paul Goode Practice Field allotment


team_list = [ team['team_name'] for team in teams.find(division_name='Upper Farm')]
faceoffs = list(combinations(team_list, 2))

print(team_list)
print(faceoffs)
for week in range(2,12):
    for slot in schedule.find(day_of_week='Saturday', week=week, field=fort_scott):
        data = dict(id=slot['id'], home_team=team['team_name'], divsion=team['division_name'])
        #schedule.update(data, ['id'])



"""
1.
Majors should start on the weekend of 2/29 and 3/1 on TI.
we should have all 10 Majors teams have a TI game scheduled for that weekend.
No other division needs a schedule for that weekend and all other schedules should start on Saturday, 3/7


3. No Friday games on TI unless absolutely necessary.

5. Lower Farm and Upper Farm have only weekend games and ends on 5/17.
(In the really nice to have, it would be good to have Upper Farm games
on Saturday and Lower Farm games all on Sunday – that will depend on
the Paul Goode Practice Field allotment and whether we want to rotate
teams through that turf field)

6. Rookie is supposed to end on May 5/17 but also have playoffs.
We should probably plan on pool play with two pools of 4 teams, and the  winner from each pool playing
a championship game on 5/17 at Tepper.  That means likely starting playoffs on or about May 4 with three
pool play games each.  That keeps more teams playing longer.
The following weekend is Memorial Day, so it would be good to get done before that.

7. PLAYOFFS
AA playoffs beginning on or about May 11,
AAA  playoffs beginning as late as May 16.
Majors playoffs beginning on May 9.
Pool play seems likely for all to keep kids playing longer.
AA, AAA and Majors finals all at Tepper on the weekend of May 30-31.

8.  Minors softball –
one game per week at Ft. Scott South on Sunday afternoon.  No other games.

9. Mid-week TI games for Majors should max out at 5 per team.

10.Mid-week TI games for AAA should max out at 3 per team.

11.No mid-week games on TI for AA or Rookie.

Nice to haves


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

