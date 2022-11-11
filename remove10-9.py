#!/usr/bin/env python3

import dataset
from datetime import datetime, timedelta
from itertools import combinations
from collections import Counter



from macros import *
from season_data import *


# Data
db = dataset.connect("sqlite:///little-league.db")

teams = db.get_table("teams")
fields = db.get_table("fields")
schedule = db.get_table("schedule")



def swap_two_slots(fromid=None, toid=None):
    print(f"Swapping {fromid} with {toid}")

    swap_from = schedule.find_one(game_id=fromid)
    print(swap_from)
    
    swap_to = schedule.find_one(game_id=toid)
    print(swap_to)

    schedule.update(
        dict(
            id=swap_to["id"],
            division=swap_from["division"],
            home_team=swap_from["home_team"],
            away_team=swap_from["away_team"],
            home_team_name=swap_from["home_team_name"],
            away_team_name=swap_from["away_team_name"],
            game_id=swap_from["game_id"],
        ),
        ["id"],
    )

    schedule.update(
        dict(
            id=swap_from["id"],
            division=swap_to["division"],
            home_team=swap_to["home_team"],
            away_team=swap_to["away_team"],
            home_team_name=swap_to["home_team_name"],
            away_team_name=swap_to["away_team_name"],
            game_id=swap_to["game_id"],
        ),
        ["id"],
    )

def apply_names():
    for division in team_name_map:
        print(f"D {division}")
        div_games = schedule.find(division=division)
        # rewrite game schedule
        for game in div_games:

            try:
                schedule.update(
                    dict(
                        id=game["id"],
                        home_team=team_name_map[game["division"]][game["home_team"]],
                        away_team=team_name_map[game["division"]][game["away_team"]],
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
                    team_name=team_name_map[division][team_data["team_name"]],
                ),
                ["id"],
            )

# Farm on Larel
#swap_two_slots("AA-19","FMU-33")

# # SWAP TB-05 and TB-02
# # SWAP TB-07 and TB-12
# # SWAP TB-16 and TB-13
# # SWAP TB-21 and TB-23
# # SWAP TB-26 and TB-27
# # SWAP TB-35 and TB-33
# # SWAP TB-31 and TB-34
# # SWAP TB-39 and TB-41
# swap_two_slots("TB-05","TB-02")
# swap_two_slots("TB-07","TB-12")
# swap_two_slots("TB-16","TB-13")
# swap_two_slots("TB-21","TB-23")
# swap_two_slots("TB-26","TB-27")
# swap_two_slots("TB-35","TB-33")
# swap_two_slots("TB-31","TB-34")
# swap_two_slots("TB-39","TB-41")


# # Lower Farm:
# # SWAP FML-04 and FML-05
# # SWAP FML-06 and FML-10
# # SWAP FML-15 and FML-13
# # SWAP FML-26 and FML-27
# swap_two_slots("FML-04","FML-05")
# swap_two_slots("FML-06","FML-10")
# swap_two_slots("FML-15","FML-13")
# swap_two_slots("FML-26","FML-27")

# # Upper Farm:
# # SWAP FMU-04 and FMU-04
# # SWAP FMU-20 and FMU-17
# # SWAP-FMU-37 and FMU-39
# #swap_two_slots("FMU-04","FMU-04")
# swap_two_slots("FMU-20","FMU-17")
# swap_two_slots("FMU-37","FMU-39")

# SWAP TB-05 and TB-03
# FMU-18 and FMU-16
# FMU-43 and FMU-45
swap_two_slots("TB-05","TB-03")
swap_two_slots("FMU-18","FMU-16")
swap_two_slots("FMU-43","FMU-45")