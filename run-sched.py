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
import functools


from macros import *
from season_data import *


myrand = 420
random.seed(myrand)

# Data
db = dataset.connect("sqlite:///little-league.db")

teams = db.get_table("teams")
fields = db.get_table("fields")
schedule = db.get_table("schedule")


fields_4660_sf = [i["field_name"] for i in fields.find(size="46/60", location="SF")]
fields_4660_all = [i["field_name"] for i in fields.find(size="46/60")]


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
        sys.stdout.write("\a")
        sys.stdout.flush()
        sys.stdout.write("\a")
        sys.stdout.flush()
        sys.stdout.write("\a")
        sys.stdout.flush()

        # time.sleep(3)


@functools.cache
def get_team_list(division):
    return [
        team["team_name"]
        for team in teams.distinct("team_name", division_name=division)
    ]


@functools.cache
def teams_in_division(division=None):
    return len(get_team_list(division))


@functools.cache
def games_per_team(division):
    division_data = teams.find_one(division_name=division)
    if division_data is None:
        return 0
    return division_data["games"]


def get_total_games(division):
    total_games = games_per_team(division) * teams_in_division(division) // 2
    return total_games


def get_faceoffs(division):
    team_list = get_team_list(division)
    total_games = get_total_games(division)

    return faceoffs.faceoffs_repeated(team_list, total_games)


def weekly_minimum(division, week=None, weeks=None):
    team_list = get_team_list(division)
    min_games = len(team_list) // 2

    total_games = get_total_games(division)
    games_per_week = total_games / weeks

    print(f"⚡ Need {total_games} total games and only have {weeks} weeks.")
    print("   Games per week is --  %0.2f" % games_per_week)
    print("   Min games is --  %0.2f" % min_games)

    min_games = games_per_week

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
    field_minutes=None,
):

    if faceoff_list is None:
        working_faceoffs = get_faceoffs(division=division)
    else:
        working_faceoffs = faceoff_list

    # print(f"    Working faceoffs: {working_faceoffs}")
    print(f"{division} - Working faceoffs count: {len(working_faceoffs)}")

    weeks = end_week - start_week

    if forced_weekly_minimum is None:
        basic_weekly_min = weekly_minimum(division, weeks=weeks)
    else:
        basic_weekly_min = forced_weekly_minimum
        print(f"Forced weekly minimum: {forced_weekly_minimum}")

    weekly_faceoffs = []

    for week in range(start_week, end_week + 1):
        # print("-" * 80)

        # BEWARE - Clever thing going on here --- randomly choose more slots to fill per week depending on ratio.
        # eg, if you need to fille 4.5 games/week, half of the time pick 4, half of the time pick 5

        (remainder, base) = math.modf(basic_weekly_min)
        add_up = random.choices([0, 1], weights=[1 - remainder, remainder])[0]
        weekly_min = int(base + add_up)

        if games_per_week_pattern:
            print("OVERRIDE GAMES PER WEEK PATTERN")
            weekly_min = games_per_week_pattern[week - 1]

        print(f"Week {week} - trying to find {weekly_min} spots for {division}")

        # Get new weekly assignments if we don't have them
        if len(weekly_faceoffs) < weekly_min:
            needed = weekly_min - len(weekly_faceoffs)

            # print(f"    Need {needed} more faceoffs")
            if len(working_faceoffs) < 1:
                print("    No more faceoffs left.. adding more")
                working_faceoffs = get_faceoffs(division=division)

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
                        field_minutes=field_minutes,
                    )
        placed = weekly_min - len(weekly_faceoffs)
        print(
            f"  Found: {placed}   Total Games Left: {len(working_faceoffs) + len(weekly_faceoffs)}"
        )

    if len(working_faceoffs) + len(weekly_faceoffs) > 0:
        stuck(division=division, todo=working_faceoffs)
    return working_faceoffs


def division_game_count(division):
    current_games_for_division = list(
        schedule.find(division=division, away_team={"not": None})
    )

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

    # print(all_slots)

    count = 0
    for checkslot in all_slots:
        if team == checkslot["home_team"] or team == checkslot["away_team"]:
            count += 1
            if count > 2:
                print(f"3in5 RULE BLOCK -- {count}")
                return False

    return True


def field_time(start, end):
    start_hour = int(start.split(":")[0])
    end_hour = int(end.split(":")[0])
    return end_hour - start_hour


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
    field_minutes=None,
):

    for week in range(start_week, end_week + 1):

        if field_minutes:
            matching_slots = list(
                schedule.find(
                    day_of_week=day_of_week,
                    week_number=week,
                    field=fields,
                    time_length=field_minutes,
                    home_team=None,
                )
            )
        else:
            matching_slots = list(
                schedule.find(
                    day_of_week=day_of_week,
                    week_number=week,
                    field=fields,
                    home_team=None,
                )
            )
        # print(f"  {len(matching_slots)} open slots found")
        # print(f"{matching_slots}")

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
            # if division == 'Rookie':
            #     if slot['field'] == "Rossi Park #1":
            #         if slot['start'] != '12:00':
            #             continue
            #     elif slot['field'] == 'Balboa Park #2 - Near Playground' and \
            #         slot['start'] == '15:00':
            #         continue

            # elif division == 'Minors AA':
            #     if slot['field'] == "Rossi Park #1" and slot['start'] != '09:00':
            #             continue
            #     elif slot['field'] ==  "Balboa Park #1 - Near Skatepark" and slot['start'] != '12:00':
            #         continue
            #     elif slot['field'] ==  "Balboa Park #2 - Near Playground" and slot['start'] != '15:00':
            #         continue
            #     elif slot['field'] ==  "Ketcham" and slot['start'] != '12:00':
            #         continue

            # elif division == 'Minors AAA':
            #     if slot['field'] == "Rossi Park #1" and slot['start'] != '15:00':
            #         continue
            #     elif slot['field'] ==  "Balboa Park #1 - Near Skatepark" and slot['start'] == '12:00':
            #         continue
            #     elif slot['field'] ==  "Tepper" and slot['start'] != '12:00':
            #         continue

            # elif division == 'Majors':
            #     if slot['field'] ==  "Tepper" and slot['start'] == '12:00':
            #         continue
            #     elif slot['field'] ==  "Ketcham" and slot['start'] != '15:00':
            #         continue

            # elif division == 'Majors':
            #     if slot['field'] ==  "Ketcham" and slot['start'] != '12:00':
            #         continue

            if slot["location"] == "TI" and slot["day_of_week"] == "Friday":
                continue  # Skip Fridays at TI

            if len(faceoff_list) == 0:
                continue  # No more work to be done

            # Candidate teams
            (a_team, b_team) = faceoff_list[:1][0]

            # print(f'Trying to place {a_team}, {b_team}')

            # Try to balance TI fiedls
            a_tepper_count = sum(
                1
                for _ in schedule.find(
                    home_team=a_team, field="Tepper", division=division
                )
            ) + sum(
                1
                for _ in schedule.find(
                    away_team=a_team, field="Tepper", division=division
                )
            )
            a_ketcham_count = sum(
                1
                for _ in schedule.find(
                    home_team=a_team, field="Ketcham", division=division
                )
            ) + sum(
                1
                for _ in schedule.find(
                    away_team=a_team, field="Ketcham", division=division
                )
            )

            # print(f'TepperA {a_tepper_count}  Ketcham {a_ketcham_count}')

            # HACK If a team's tepper count is highter than ketcham count, and current field is Tepper, skip slot
            # if a_tepper_count > a_ketcham_count and slot['field'] == 'Tepper':
            #     print('TOO MUCH A TEPPER')
            #     continue

            b_tepper_count = sum(
                1
                for _ in schedule.find(
                    home_team=b_team, field="Tepper", division=division
                )
            ) + sum(
                1
                for _ in schedule.find(
                    away_team=b_team, field="Tepper", division=division
                )
            )
            b_ketcham_count = sum(
                1
                for _ in schedule.find(
                    home_team=b_team, field="Ketcham", division=division
                )
            ) + sum(
                1
                for _ in schedule.find(
                    away_team=b_team, field="Ketcham", division=division
                )
            )

            # print(f'TepperB {b_tepper_count}  Ketcham {b_ketcham_count}')

            # HACK If a team's tepper count is highter than ketcham count, and current field is Tepper, skip slot
            # if b_tepper_count > b_ketcham_count and slot['field'] == 'Tepper':
            #     print('TOO MUCH B TEPPER')
            #     continue

            if division == "Rookie":
                # Week 7 for rookie at Tepper
                if slot["field"] == "Tepper" or slot["field"] == "Ketcham":
                    if slot["week_number"] != "7":
                        continue

            elif division == "Minors AA":
                # Week 8 at tepper is a special case
                if slot["field"] == "Tepper":
                    if slot["week_number"] != "8":
                        # print(f"tepper exlusioin at {slot}")
                        continue

                # Adjust week 7 at tepper issue
                if slot["week_number"] == "7":
                    if slot["field"] == "West Sunset #3":
                        continue
                    elif slot["field"] == "Sunset Rec":
                        continue
                    # if a_tepper_count > 0 or b_tepper_count > 0:
                    #     continue

            elif division == "Minors AAA":
                # Adjust week 7 at tepper issue
                if slot["week_number"] == "7":
                    if slot["field"] == "Ft. Scott - North":
                        continue
                if slot["field"] == "Tepper":
                    if a_tepper_count > 1 or b_tepper_count > 1:
                        print("too much tepper")
                        continue

            elif division == "Majors":
                if slot["field"] == "Tepper":
                    if a_tepper_count + b_tepper_count > 5:
                        print("too much tepper")
                        continue

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
                    swap_teams = False

                ## if you have more than 5 home games for your team, swap
                myhomegames = sum(
                    1 for _ in schedule.find(home_team=a_team, division=division)
                )
                if myhomegames > 4:

                    swap_teams = True

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

            if division in team_name_map:
                home_team_name = team_name_map[division][home_team]
                away_team_name = team_name_map[division][away_team]
            else:
                home_team_name = home_team
                away_team_name = away_team

            print(
                f"    ✅ Assigned {slot['day_of_week']: <10} {slot['datestamp']} @ {slot['field']: <20} to {division: <15} - {home_team: <7} vs {away_team: <7}"
            )
            data = dict(
                id=slot["id"],
                home_team=home_team,
                home_team_name=home_team_name,
                away_team=away_team,
                away_team_name=away_team_name,
                division=division,
                game_id=game_id,
            )
            schedule.update(data, ["id"])

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


def count_ti(division=None, team=None):
    total = 0
    for field in ["Tepper", "Ketcham"]:
        # print(f'{field} - {team} - {division}')
        homes = list(schedule.find(division=division, home_team=team, field=field))
        # print(f'H: {len(homes)} -- {homes}')
        total += len(homes)
        aways = list(schedule.find(division=division, away_team=team, field=field))
        # print(f'A: {len(aways)} --  {aways}')

        total += len(aways)
        # print(total)
    return total


def count_fields(division=None, team=None, checkfields=[]):
    results = {}
    total = 0
    for field in checkfields:
        total = 0
        print(f"{field} - {team} - {division}")
        homes = list(schedule.find(division=division, home_team=team, field=field))
        total += len(homes)
        aways = list(schedule.find(division=division, away_team=team, field=field))

        total += len(aways)
        results[field] = total
    return results


def field_count(division=None, team=None, checkfield=None):
    total = 0
    # print(f'{division} - {team} - {checkfield}')
    homes = list(schedule.find(division=division, home_team=team, field=checkfield))
    aways = list(schedule.find(division=division, away_team=team, field=checkfield))

    total += len(homes) + len(aways)
    return total


def clear_schedule(division=None):
    print(f"Erasing {division}")
    div_games = list(schedule.find(division=division))
    print(f"{len(list(div_games))} games to erase")

    for slot in div_games:
        # print(slot["id"])
        try:
            data = dict(
                id=slot["id"],
                home_team=None,
                home_team_name=None,
                away_team=None,
                away_team_name=None,
                division=None,
                game_id=None,
            )
            schedule.update(data, ["id"])
        except KeyError as e:
            print(f"Unknown slot found {e}")

    # results
    div_games = schedule.find(division=division)
    print(f"{len(list(div_games))} games still here")


##########################################################################################
### Main schedule:


def analyze_schedule(
    division=None,
    checkfields=["Tepper", "Ketcham"],
    checkmax=6,
    deviations=1.5,
    checkzero=False,
    checkzerotepper=False,
    teppermin=None,
):
    measure_counts = {}
    for field in checkfields:
        for team in get_team_list(division):
            count = field_count(division=division, team=team, checkfield=field)
            measure_counts[team] = count
            # print(f"Team {team}, Field {field}, Count {measure_counts[team]}")
        values = list(measure_counts.values())
        deviation = round(statistics.stdev(values), 2)
        if deviation == 0:
            deviation = 0.01

        mean = round(statistics.mean(values), 2)
        print(f"{field} \t{values}\t{deviation}\t{mean}    teppermin {teppermin}")

        calc_deviations = round(abs(measure_counts[team] - mean) / deviation, 2)

        if teppermin is None:
            if deviation < 1.05:
                # early skip for low deviation
                print("ok")
                continue

        for team in measure_counts:

            if teppermin is not None:
                if field == "Tepper":
                    if measure_counts[team] < teppermin:
                        print(
                            f"{team} - {measure_counts[team]} - not enough tepper {teppermin}"
                        )
                        return False

            if (
                measure_counts[team] > mean + deviations * deviation
                and measure_counts[team] > 2
            ):
                print(
                    f"{team} has {measure_counts[team]} which is {calc_deviations} more than deviations from the mean {mean}"
                )
                return False
            if measure_counts[team] > checkmax:
                print(
                    f"{team} has {measure_counts[team]} which is more than {checkmax} -- we can do better {list(values)}"
                )
                return False
            if checkzero and measure_counts[team] == 0:
                print(
                    f"RAND:{myrand} - Team {team} has {measure_counts[team]} -- we can do better {list(values)} "
                )
                return False
            if checkzerotepper and field == "Tepper" and measure_counts[team] == 0:
                print(
                    f"RAND:{myrand} - Team {team} has {measure_counts[team]} teppper -- we can do better {list(values)} "
                )
                return False
    return True


def loop_schedule(
    division=None,
    start_week=1,
    end_week=9,
    day_of_week_prefs=[["Sunday"]],
    forced_weekly_minimum=6,
    field_prefs=[],
    field_minutes=None,
    checkfields=["Tepper", "Ketcham"],
    checkmax=6,
    checkzero=False,
    checkzerotepper=False,
    teppermin=None,
    deviations=1.5,
    myrand=999,
):

    while True:
        print("=" * 60)
        print(f"Random: {myrand}")
        random.seed(myrand)
        schedule_by_week(
            division=division,
            start_week=start_week,
            end_week=end_week,
            day_of_week_prefs=day_of_week_prefs,
            forced_weekly_minimum=forced_weekly_minimum,
            field_prefs=field_prefs,
            field_minutes=field_minutes,
        )

        if (
            analyze_schedule(
                division=division,
                checkfields=checkfields,
                checkmax=checkmax,
                deviations=deviations,
                checkzero=checkzero,
                checkzerotepper=checkzerotepper,
                teppermin=teppermin,
            )
            == True
        ):
            print(f"{division} schedule is good {myrand}")
            break
        else:
            print(f"{division} schedule is bad {myrand}")
            clear_schedule(division=division)
            myrand = int(myrand) + 1


# Teeball
myfields = ["Presidio Wall", "Rossi Park #1", "Laurel Hill"]
loop_schedule(
    division="Tee Ball",
    field_prefs=[
        ["Presidio Wall", "Laurel Hill", "Rossi Park #1"],
        ["Presidio Wall", "Rossi Park #1", "Laurel Hill"],
    ],
    field_minutes=120,
    checkfields=myfields,
    myrand=444,
    checkmax=6,
)


loop_schedule(
    division="Farm - Lower",
    field_prefs=[
        ["Presidio Wall", "Paul Goode Practice"],
        [
            "Paul Goode Practice",
            "Presidio Wall",
            "Rossi Park #1",
            "Ft. Scott - South",
            "Visitation Valley",
        ],
        [
            "Paul Goode Practice",
            "Presidio Wall",
            "Rossi Park #1",
            "Visitation Valley",
            "Ft. Scott - South",
        ],
    ],
    checkfields=["Paul Goode Practice", "Ft. Scott - South"],
    myrand=622,
    forced_weekly_minimum=5,
    checkmax=4,
)


loop_schedule(
    division="Farm - Upper",
    forced_weekly_minimum=5,
    field_prefs=[
        ["Balboa D2"],
        ["Rossi Park #1"],
        [
            "Paul Goode Practice",
            "Presidio Wall",
            "Rossi Park #1",
            "Visitation Valley",
            "Ft. Scott - South",
            "Laurel Hill",
        ],
        ["Ft. Scott - South", "Ft. Scott - North", "Laurel Hill"],
    ],
    myrand=635,
    checkfields=["Ft. Scott - South", "Visitation Valley", "Laurel Hill"],
    checkmax=6,
)


loop_schedule(
    division="Rookie",
    forced_weekly_minimum=6,
    field_prefs=[
        ["Tepper", "Ketcham"],
        ["Palega"],
        ["Visitation Valley"],
        [
            "Ft. Scott - South",
            "Laurel Hill",
            "Parkside",
            "Presidio Wall",
            "Rossi Park #1",
            "Visitation Valley",
            "Ft. Scott - South",
            "Balboa D2",
            "Crocker D3",
            # "Palega",
        ],
        ["Laurel Hill", "Parkside", "Balboa D2", "Ft. Scott - South", "Sunset Rec"],
    ],
    myrand=884,
    checkfields=["Laurel Hill", "Parkside", "Sunset Rec"],
    checkmax=6,
    deviations=1.5,
)

loop_schedule(
    division="Minors AA",
    forced_weekly_minimum=3,
    field_prefs=[
        ["Tepper"],
        [
            "Laurel Hill",
            "Sunset Rec",
            "West Sunset #3",
            "Crocker D3",
            "Parkside",
            "Tepper",
        ],
        ["Parkside", "Ft. Scott - North", "Ft. Scott - South"],
        [
            "Tepper",
            "Ketcham",
        ],
    ],
    checkfields=["West Sunset #3"],
    checkmax=4,
    myrand=1005,
)


loop_schedule(
    division="Minors AAA",
    forced_weekly_minimum=4,
    field_prefs=[
        [
            "Sunset Rec",
            "West Sunset #3",
            "Balboa D2",
            "Crocker D3",
            "Parkside",
            "Ft. Scott - North",
            "Ft. Scott - South",
            "Tepper",
        ],
        ["Tepper", "Ketcham", "Parkside", "Ft. Scott - North", "Ft. Scott - South"],
    ],
    checkfields=["West Sunset #3", "Ketcham", "Tepper"],
    checkmax=5,
    checkzero=False,
    checkzerotepper=True,
    myrand=1,
    deviations=2,
)

loop_schedule(
    division="Majors",
    forced_weekly_minimum=5,
    field_prefs=[
        [
            "Sunset Rec",
            "West Sunset #3",
            "Balboa D2",
            "Crocker D3",
            "Ft. Scott - North",
            "Tepper",
            "Ketcham",
            "Laurel Hill",
            "Palega",
        ],
        ["Tepper", "Ketcham", "Parkside", "Ft. Scott - North", "Ft. Scott - South"],
        [
            "Tepper",
            "Ketcham",
            "Parkside",
            "Ft. Scott - North",
            "Ft. Scott - South",
            "Laurel Hill",
        ],
    ],
    checkfields=["Ketcham", "Tepper"],
    checkmax=5,
    myrand=1309,
    checkzerotepper=True,
    teppermin=2,
    deviations=1.6,
)

loop_schedule(
    division="Juniors",
    forced_weekly_minimum=4,
    field_prefs=[["Paul Goode Main", "West Sunset #1", "Balboa Sweeney"]],
    checkfields=["West Sunset #1", "Paul Goode Main", "Balboa Sweeney"],
    checkmax=5,
    myrand=1068,
)


loop_schedule(
    division="Seniors",
    forced_weekly_minimum=2,
    field_prefs=[["West Sunset #1", "Paul Goode Main", "Balboa Sweeney"]],
    checkfields=["West Sunset #1", "Paul Goode Main", "Balboa Sweeney"],
    checkmax=6,
    myrand=1068,
)
sys.exit()


random.seed("374")


def swap_ids(fromid=None, toid=None):
    swap_from = schedule.find_one(game_id=fromid)
    swap_to = schedule.find_one(game_id=toid)

    h1 = swap_from["home_team"]
    h2 = swap_to["home_team"]

    a1 = swap_from["away_team"]
    a2 = swap_to["away_team"]

    schedule.update(
        dict(
            id=swap_to["id"],
            home_team=h1,
            away_team=a1,
        ),
        ["id"],
    )

    schedule.update(
        dict(
            id=swap_from["id"],
            home_team=h2,
            away_team=a2,
        ),
        ["id"],
    )


for division in div_teams:
    print(f"D {division}")
    div_games = schedule.find(division=division)
    # rewrite game schedule
    for game in div_games:
        try:
            schedule.update(
                dict(
                    id=game["id"],
                    home_team=div_teams[game["division"]][game["home_team"]],
                    away_team=div_teams[game["division"]][game["away_team"]],
                ),
                ["id"],
            )
        except KeyError as e:
            print(f"Uknown Team found {e}")

    # rewrite team names
    all_teams = teams.find(division_name=division)
    for team_data in all_teams:  # .distinct('team_name', division_name=division):
        # print(team_data)
        teams.update(
            dict(
                id=team_data["id"],
                team_name=div_teams[division][team_data["team_name"]],
            ),
            ["id"],
        )
