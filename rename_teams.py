#!/usr/bin/env python3


import dataset

from season_data import team_name_map

# Data
db = dataset.connect("sqlite:///little-league.db")

teams = db.get_table("teams")
fields = db.get_table("fields")
schedule = db.get_table("schedule")


for division in team_name_map:
    print(f"D {division}")
    div_games = schedule.find(division=division)
    # rewrite game schedule
    for game in div_games:
        try:
            schedule.update(
                dict(
                    id=game["id"],
                    home_team_name=team_name_map[game["division"]][game["home_team"]],
                    away_team_name=team_name_map[game["division"]][game["away_team"]],
                ),
                ["id"],
            )
        except KeyError as e:
            print(f"Uknown Team found {e}")

    # rewrite team names
    # all_teams = teams.find(division_name=division)
    # for team_data in all_teams:  # .distinct('team_name', division_name=division):
    #     # print(team_data)
    #     teams.update(
    #         dict(
    #             id=team_data["id"],
    #             team_name=team_name_map[division][team_data["team_name"]],
    #         ),
    #         ["id"],
    #     )