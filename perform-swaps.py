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
swap_two_slots("AA-19","FMU-33")