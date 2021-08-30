#!/usr/bin/env python3

import dataset
from datetime import datetime, timedelta
from itertools import combinations
from collections import Counter
import faceoffs
import math
import random
import sys
import time
import statistics

try:
    myrand = sys.argv[1]
except:
    myrand = 2020

random.seed(2021)

# Data
db = dataset.connect("sqlite:///little-league.db")

teams = db.get_table("teams")
fields = db.get_table("fields")
schedule = db.get_table("schedule")

# helpers
fort_scott = ["Ft. Scott - North", "Ft. Scott - South"]
farm_scott_goode = ["Ft. Scott - South", "Paul Goode Practice"]
tepper_ketcham = ["Tepper", "Ketcham"]
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
monday_thursday = ["Monday", "Tuesday", "Wednesday", "Thursday","Saturday","Sunday"]
tuesday_thursday = ["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]

anyday_but_friday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]
fields_4660_sf = [i["field_name"] for i in fields.find(size="46/60", location="SF")]
fields_4660_all = [i["field_name"] for i in fields.find(size="46/60")]


short_division_names = {
    "Farm - Lower": "FML",
    "Farm - Upper": "FMU",
    "Rookie": "RK",
    "Minors AA": "AA",
    "Minors AAA": "AAA",
    "Majors": "MAJ",
    "Juniors": "JRS",
    "Seniors": "SRS",
    "Softball": "SFT",

}

##########################################################################################
##########################################################################################
### Reservations

# print(
#     "RESERVATION 2021-1 Softball should be assigned 1 slot at Ketcham on Sundays at 2 pm."
# )
# for slot in schedule.find(day_of_week="Sunday", start="14:00", field=["Ketcham"]):

#     print(
#         f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto Softball"
#     )
#     data = dict(
#         id=slot["id"], home_team="RESERVED", away_team="RESERVED", division="Softball"
#     )
#     schedule.update(data, ["id"])

# Farm has one game per weekend only and it must be on Ft. Scott on Sunday.
# print('RESERVATION 4 - Farm Sundays')
# for week in range(1,7):
#     for slot in schedule.find(day_of_week='Sunday',
#                 week_number=week, infield='dirt', field='Ft. Scott - South',
#                 order_by=['-datestamp'], _limit=1):
#         print(f"Reserved {slot['day_of_week']}\t{slot['datestamp']} \t{slot['field']}\tto Farm")
#         data = dict(id=slot['id'], home_team='RESERVED', division='Farm')
#         schedule.update(data, ['id'])


##########################################################################################
##########################################################################################
stuck_todo = {}


def stuck(division=None, todo=None):
    remain = len(list(schedule.find(home_team=None)))
    remain_weekday_sf = len(
        list(
            schedule.find(
                home_team=None, day_of_week=monday_thursday, fields=fields_4660_sf
            )
        )
    )
    remain_sf = len(list(schedule.find(home_team=None, fields=fields_4660_sf)))

    print("=" * 80)
    print(f"STUCK - {myrand}")
    print(f"Remaining Slots: {remain}")
    print(f"Remaining SF Weekday Slots: {remain_weekday_sf}")
    print(f"Remaining SF Slots: {remain_sf}")
    stuck_todo[division] = todo
    print("❌ STUCK:", stuck_todo)
    if int(remain) < 82:
        sys.stdout.write('\a')
        sys.stdout.flush()
        sys.stdout.write('\a')
        sys.stdout.flush()
        sys.stdout.write('\a')
        sys.stdout.flush()

        time.sleep(3)

    sys.exit(1)
    # 157


def get_team_list(division):
    return [
        team["team_name"]
        for team in teams.distinct("team_name", division_name=division)
    ]


def get_total_games(division):
    division_data = teams.find_one(division_name=division)
    games_per_team = division_data["games"]

    team_list = get_team_list(division)

    total_games = games_per_team * len(team_list) // 2
    return total_games


def get_faceoffs(division):
    team_list = get_team_list(division)
    total_games = get_total_games(division)

    faceoff_list = faceoffs.faceoffs_repeated(team_list, total_games)
    # print("=" * 80)
    # print(
    #     f"Division: {division}\n\tTeams: {len(team_list)}\n\tTotal Games: {total_games} -- {myrand}"
    # )

    return faceoff_list


def weekly_minimum(division, week=None, weeks=None):
    team_list = get_team_list(division)
    min_games = len(team_list) // 2

    total_games = get_total_games(division)
    games_per_week = total_games / weeks

    print(f"⚡ Need {total_games} total games and only have {weeks} weeks.")
    print("   Games per week is --  %0.2f" % games_per_week)
    print("   Min games is --  %0.2f" % min_games)

    min_games = games_per_week

    # if total_games/weeks > min_games:
    #     games_per_week = total_games/weeks

    #     min_games = total_games/weeks

    return min_games


def schedule_by_week(
    division=None,
    start_week=None,
    end_week=None,
    day_of_week_prefs=None,
    field_prefs=None,
    faceoff_list=None,
    weekend_percent=None,
    games_per_week_pattern=None,
    forced_weekly_minimum=None,
):

    if faceoff_list is None:
        working_faceoffs = get_faceoffs(division=division)
    else:
        working_faceoffs = faceoff_list

    #print(f"    Working faceoffs: {working_faceoffs}")

    # # Chosse a random spot in the faceoff list:
    # cut_spot = random.randint(0, len(working_faceoffs))
    # print(f"Cut: {cut_spot}")
    # working_faceoffs0 = working_faceoffs[cut_spot:] + working_faceoffs[:cut_spot]
    # working_faceoffs = working_faceoffs0

    weeks = end_week - start_week

    if forced_weekly_minimum is None:
        basic_weekly_min = weekly_minimum(division, weeks=weeks)
    else:
        basic_weekly_min = forced_weekly_minimum

    weekly_faceoffs = []

    for week in range(start_week, end_week + 1):
        #print("-" * 80)

        # BEWARE - Clever thing going on here --- randomly choose more slots to fill per week depending on ratio.
        # eg, if you need to fille 4.5 games/week, half of the time pick 4, half of the time pick 5

        (remainder, base) = math.modf(basic_weekly_min)
        add_up = random.choices([0, 1], weights=[1 - remainder, remainder])[0]
        weekly_min = int(base + add_up)

        if games_per_week_pattern:
            print("OVERRIDE GAMES PER WEEK PATTERN")
            weekly_min = games_per_week_pattern[week - 1]

        # print(
        #     f"Week {week} - trying to find {weekly_min} spots for {division} - based on {basic_weekly_min}"
        # )

        # Get new weekly assignments if we don't have them
        if len(weekly_faceoffs) < weekly_min:
            needed = weekly_min - len(weekly_faceoffs)

            weekly_faceoffs = weekly_faceoffs + working_faceoffs[:needed]
            # shrink total working list
            working_faceoffs = working_faceoffs[needed:]

        for day_of_week in day_of_week_prefs:
            for fields in field_prefs:
                if len(weekly_faceoffs) > 0:
                    weekly_faceoffs = complex_assign(
                        division=division,
                        day_of_week=day_of_week,
                        start_week=week,
                        end_week=week,
                        fields=fields,
                        faceoff_list=weekly_faceoffs,
                    )
        placed = weekly_min - len(weekly_faceoffs)
        # print(
        #     f"Found: {placed}   Total Games Left: {len(working_faceoffs) + len(weekly_faceoffs)} -- {myrand}"
        # )

    if len(working_faceoffs) + len(weekly_faceoffs) > 0:
        stuck(division=division, todo=working_faceoffs)
    return working_faceoffs


def division_game_count(division):
    current_games_for_division = list(
        schedule.find(division=division, away_team={"not": None})
    )
    # print(current_games_for_division)

    return (len(current_games_for_division)) + 1


def safe_to_schedule(division, day_of_year, team):
    # Checks to see if current team already has a game schedule today, yesterday or tomorrow

    prior_day_slots = list(
        schedule.find(day_of_year=str(day_of_year - 1), division=division)
    )
    same_day_slots = list(
        schedule.find(day_of_year=str(day_of_year), division=division)
    )
    next_day_slots = list(
        schedule.find(day_of_year=str(day_of_year + 1), division=division)
    )
    all_slots = prior_day_slots + same_day_slots + next_day_slots

    for checkslot in all_slots:
        if team == checkslot["home_team"] or team == checkslot["away_team"]:
            return False

    return True


def three_games_in_five_days(division, day_of_year, team):
    # Checks to see if team would have 3 games in 5 day window

    five_prior_day_slots = list(
        schedule.find(day_of_year=str(day_of_year - 5), division=division)
    )

    four_prior_day_slots = list(
        schedule.find(day_of_year=str(day_of_year - 4), division=division)
    )

    three_prior_day_slots = list(
        schedule.find(day_of_year=str(day_of_year - 3), division=division)
    )
    two_prior_day_slots = list(
        schedule.find(day_of_year=str(day_of_year - 2), division=division)
    )
    prior_day_slots = list(
        schedule.find(day_of_year=str(day_of_year - 1), division=division)
    )
    same_day_slots = list(
        schedule.find(day_of_year=str(day_of_year), division=division)
    )
    next_day_slots = list(
        schedule.find(day_of_year=str(day_of_year + 1), division=division)
    )
    two_next_day_slots = list(
        schedule.find(day_of_year=str(day_of_year + 2), division=division)
    )

    all_slots = ( 
        five_prior_day_slots
        + four_prior_day_slots
        + three_prior_day_slots
        + two_prior_day_slots
        + prior_day_slots
        + same_day_slots
        + next_day_slots
        + two_next_day_slots
    )

    #print(all_slots)

    count = 0
    for checkslot in all_slots:
        if team == checkslot["home_team"] or team == checkslot["away_team"]:
            count += 1
            if count > 2:
                print(f"3in5 RULE BLOCK -- {count}")
                return False

    return True


def complex_assign(
    division=None,
    start_week=None,
    end_week=None,
    day_of_week=None,
    fields=None,
    max_per_week=None,
    faceoff_list=None,
    max_per_week_pattern=None,
    weekend_percent=None,
):

    #print(f"  Checking for slots on {day_of_week} at {fields}")

    for week in range(start_week, end_week + 1):
        matching_slots = list(
            schedule.find(day_of_week=day_of_week, week_number=week, field=fields, home_team=None)
        )
        #print(f"  {len(matching_slots)} open slots found")
        #print(f"{matching_slots}")

        # Shuffle the usable slots (more fair results)
        random.shuffle(matching_slots)

        for slot in matching_slots:
            if slot["home_team"] is not None:

                continue  # already booked

            # if  slot['field'] == 'Ft. Scott - North' and \
            #         slot['day_of_week'] == 'Friday' and \
            #         slot['start'] == '19:00' and \
            #         ( division == 'Minors AA' or division == 'Minors AAA' ) :
            #     continue # Skip  Minors at late slot in FSN

            # Ugly -- exclusions 
            if division == 'Rookie':
                if slot['field'] == "Rossi Park #1":
                    if slot['start'] != '12:00':
                        continue
                elif slot['field'] == 'Balboa Park #2 - Near Playground' and \
                    slot['start'] == '15:00':
                    continue

            elif division == 'Minors AA':
                if slot['field'] == "Rossi Park #1" and slot['start'] != '09:00':
                        continue
                elif slot['field'] ==  "Balboa Park #1 - Near Skatepark" and slot['start'] != '12:00':
                    continue
                elif slot['field'] ==  "Balboa Park #2 - Near Playground" and slot['start'] != '15:00':
                    continue
                elif slot['field'] ==  "Ketcham" and slot['start'] != '12:00':
                    continue

            elif division == 'Minors AAA':
                if slot['field'] == "Rossi Park #1" and slot['start'] != '15:00':
                    continue 
                elif slot['field'] ==  "Balboa Park #1 - Near Skatepark" and slot['start'] == '12:00':
                    continue
                elif slot['field'] ==  "Tepper" and slot['start'] != '12:00':
                    continue

            elif division == 'Majors':
                if slot['field'] ==  "Tepper" and slot['start'] == '12:00':
                    continue
                elif slot['field'] ==  "Ketcham" and slot['start'] != '15:00':
                    continue

            elif division == 'Majors':
                if slot['field'] ==  "Ketcham" and slot['start'] != '12:00':
                    continue




            if slot["location"] == "TI" and slot["day_of_week"] == "Friday":
                continue  # Skip Fridays at TI

            if len(faceoff_list) == 0:
                continue  # No more work to be done

            # Candidate teams
            (a_team, b_team) = faceoff_list[:1][0]
            #print(f"Trying to place a game between {a_team} and {b_team}")

            # Conflict checking
            day_of_year = int(slot["day_of_year"])

            if (
                safe_to_schedule(division, day_of_year, a_team)
                and safe_to_schedule(division, day_of_year, b_team)
                and three_games_in_five_days(division, day_of_year, a_team)
                and three_games_in_five_days(division, day_of_year, b_team)
            ):
                ####################################################################################################
                # Balance home/away

                # Check for prior same matchup
                prior_matchups = sum(
                    1
                    for _ in schedule.find(
                        home_team=a_team, away_team=b_team, division=division
                    )
                )
                if prior_matchups == 1:
                    swap_teams = True
                else:
                    # Use counting method
                    a_home_game_count = sum(
                        1 for _ in schedule.find(home_team=a_team, division=division)
                    )
                    b_home_game_count = sum(
                        1 for _ in schedule.find(home_team=b_team, division=division)
                    )
                    if (
                        a_home_game_count >= b_home_game_count
                        and a_home_game_count != 0
                    ):
                        swap_teams = True
                    else:
                        swap_teams = False

                # Apply swap
                try:
                    if swap_teams:
                        (away_team, home_team) = faceoff_list.pop(0)
                    else:
                        (home_team, away_team) = faceoff_list.pop(0)

                except:
                    # No games left to assign
                    continue

                ##########
                # create unique game ID
                game_id = "%s-%02d" % (
                    short_division_names[division],
                    division_game_count(division=division),
                )

                # print(
                #     f"    ✅ Assigned {slot['day_of_week']: <10} {slot['datestamp']} @ {slot['field']: <20} to {division: <15} - {home_team: <7} vs {away_team: <7}"
                # )
                data = dict(
                    id=slot["id"],
                    home_team=home_team,
                    away_team=away_team,
                    division=division,
                    game_id=game_id,
                )
                schedule.update(data, ["id"])
        else:
            pass
            #print("Unable to schedule any more.")

    return faceoff_list


##########################################################################################
# Swap functions
def get_schedule_day(day_of_year=None):
    for id in get_ids(day_of_year=day_of_year):
        print(id)
        print(get_slot(id=id))


def get_ids(day_of_year=None):
    return [slot["id"] for slot in list(schedule.find(day_of_year=day_of_year))]


def get_slot(id=None):
    return schedule.find_one(id=id)


def count_tepper(team=None, division=None, field="Tepper"):

    homes = list(
        schedule.find(division=division, home_team=team, week_number=1, field=field)
    )
    aways = list(
        schedule.find(division=division, away_team=team, week_number=1, field=field)
    )

    return len(homes) + len(aways)



def count_ti(division=None, team=None):
    total = 0
    for field in ['Tepper', "Ketcham"]:
        # print(f'{field} - {team} - {division}')
        homes = list(
            schedule.find(division=division, 
                home_team=team, field=field)
        )
        # print(f'H: {len(homes)} -- {homes}')
        total += len(homes)
        aways = list(
            schedule.find(division=division, 
                away_team=team, field=field)
        )
        # print(f'A: {len(aways)} --  {aways}')

        total += len(aways)
        #print(total)
    return total

def count_foo(division=None, team=None, foo=[]):
    total = 0
    for field in foo:
        homes = list(
            schedule.find(division=division, 
                home_team=team, field=field)
        )
        total += len(homes)
        aways = list(
            schedule.find(division=division, 
                away_team=team, field=field)
        )

        total += len(aways)
    return total




##########################################################################################
### Main schedule:

# Farm
schedule_by_week(
    division="Farm - Lower",
    start_week=1,
    end_week=9,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=3,
    # field_prefs=[['Ft. Scott - South']]
    field_prefs=[["Paul Goode Practice"]]
)


schedule_by_week(
    division="Farm - Upper",
    start_week=1,
    end_week=9,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=3,
    field_prefs=[["Julias Kahn along Presidio Wall"]]
)

schedule_by_week(
    division="Rookie",
    start_week=1,
    end_week=9,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=3,
    field_prefs=[["Balboa Park #2 - Near Playground", "Rossi Park #1"]]
)


random.seed('134')
schedule_by_week(
    division="Minors AA",
    start_week=1,
    end_week=7,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=4,
    field_prefs=[["Balboa Park #1 - Near Skatepark", "Balboa Park #2 - Near Playground", "Rossi Park #1", "Ketcham"]]
)

random.seed('337')
schedule_by_week(
    division="Minors AAA",
    start_week=1,
    end_week=7,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=4,
    field_prefs=[["Balboa Park #1 - Near Skatepark", "Rossi Park #1", "Tepper"]]
)

random.seed('403')
#random.seed(myrand)
schedule_by_week(
    division="Majors",
    start_week=1,
    end_week=7,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=5,
    field_prefs=[[
        'West Sunset #3',
         "Tepper", 
         "Ketcham"]]
)

# div='Majors'
# measure_counts = {}
# for team in get_team_list(div):
#     mycount = count_foo(division=div, team=team, foo=['Tepper', "Ketcham"])
#     #print(f"Team {team}, Count {mycount}")
#     measure_counts[team] = mycount

# values = measure_counts.values()
# deviation = round(statistics.stdev(values),2)

# for team in measure_counts:
#     if measure_counts[team] > 4:
#         print(f'RAND:{myrand} DEV:{deviation} - Team {team} has {measure_counts[team]} -- we can do better {list(values)}')
#         sys.exit(1)
#     elif measure_counts[team] == 0:
#         print(f'RAND:{myrand} - Team {team} has {measure_counts[team]} -- we can do better {list(values)} ')
#         sys.exit(1)


random.seed('374')
schedule_by_week(
    division="Juniors",
    start_week=1,
    end_week=7,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=4,
    field_prefs=[[
        'West Sunset #2',
         "Paul Goode Main",]]
)






# print(f'RAND: {myrand} DEV:{deviation} - {values}')
# print(f'happy {myrand}')
#sys.exit(0)

schedule_by_week(
    division="Seniors",
    start_week=1,
    end_week=7,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=2,
    field_prefs=[[
        'West Sunset #1']]
)

schedule_by_week(
    division="Softball",
    start_week=1,
    end_week=9,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=2,
    field_prefs=[[
        'Ketcham']]
)





def swap_ids(fromid=None, toid=None):
    swap_from = schedule.find_one(game_id=fromid)
    swap_to = schedule.find_one(game_id=toid)


    h1 = swap_from['home_team']
    h2 = swap_to['home_team']

    a1 = swap_from['away_team']
    a2 = swap_to['away_team']

    schedule.update(
        dict(
            id=swap_to['id'],
            home_team=h1,
            away_team=a1,
        ),
        ["id"],
    )

    schedule.update(
        dict(
            id=swap_from['id'],
            home_team=h2,
            away_team=a2,
        ),
        ["id"],
    )



# 2021 swaps
#swap_ids()

swap_ids(fromid='FML-04', toid='FML-05')
swap_ids(fromid='FML-08', toid='FML-07')
swap_ids(fromid='FML-10', toid='FML-11')
swap_ids(fromid='FML-13', toid='FML-15')
swap_ids(fromid='FML-16', toid='FML-17')
swap_ids(fromid='FML-23', toid='FML-24')
swap_ids(fromid='FML-25', toid='FML-27')


swap_ids(fromid='FMU-01', toid='FMU-02')

swap_ids(fromid='RK-19', toid='RK-21')
swap_ids(fromid='RK-22', toid='RK-24')




#Apply Team names:

div_teams = {
    'Farm - Lower' : {              
                "Team 1": 'Angels', 
                "Team 2": 'Cubs', 
                "Team 3": 'Red Sox', 
                "Team 4": 'White Sox',
                "Team 5": 'Giants', 
                "Team 6": 'Athletics'
    },
    'Farm - Upper' : {              
                "Team 1": 'Cubs', 
                "Team 4": 'Angels', 
                "Team 2": 'Red Sox', 
                "Team 3": 'White Sox',
                "Team 6": 'Giants', 
                "Team 5": 'Athletics'
    },
    'Rookie' : {              
                "Team 2": "Cubs (Lang/OBrien)", 
                "Team 3": 'Angels (Defoor/Gates)', 
                "Team 5": 'Red Sox (Groban/Buttorf)', 
                "Team 6": 'White Sox (McDowell/Bagley)',
                "Team 4": 'Giants (Evans/Berning)', 
                "Team 1": 'Athletics (MacFarlane/Yarger)'
    }    
}

for division in div_teams:
    print(f'D {division}')
    div_games = schedule.find(division=division)
    # rewrite game schedule
    for game in div_games:
        try:
            schedule.update(
                dict(
                    id=game['id'],
                    home_team=div_teams[game['division']][game['home_team']],
                    away_team=div_teams[game['division']][game["away_team"]],
                ),
                ["id"],
            )
        except KeyError as e:
            print(f'Uknown Team found {e}')

    # rewrite team names
    all_teams = teams.find(division_name=division)
    for team_data in all_teams:  # .distinct('team_name', division_name=division):
        #print(team_data)
        teams.update(
            dict(
                id=team_data['id'],
                team_name = div_teams[division][team_data['team_name']]
            ),
            ["id"],
        )


    # if division == 'Farm - Upper':
    #     for name in ['Cubs', 'Red Sox', 'White Sox', 'Angels', 'Athletics', 'Giants']:
    #         data['team_name'] = name
    #         table.insert(data)

    # if division == 'Farm - Lower':
    #     for name in [
    #             'Angels', 
    #             'Cubs', 
    #             'Red Sox', 
    #             'White Sox',
    #             'Giants', 
    #             'Athletics', 
    #             ]:
    #         data['team_name'] = name
    #         table.insert(data)

# print(f'DEBUG: rand was 124')
# div='Rookie'
# counts = Counter()
# for team in get_team_list(div):
#     count = count_tepper(division=div, team=team)
#     print(f"Team {team}, Count {count}")
#     counts[count] += 1
#     if count > 1:
#         sys.exit(1)

# for c in [0,1,2,3]:
#     print("counts",c,counts[c])
# if counts[0] == 1:
#     print("0 was 1")
#     #sys.exit(1)

random.seed(1974)

