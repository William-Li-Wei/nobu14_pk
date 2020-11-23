import pandas as pd
import numpy as np

from src.Team import Team
import config as conf


s_zhentianchangxing = conf.WARRIORS.loc[25]
s_zhentianxingcun = conf.WARRIORS.loc[26]
s_wutianxinxuan = conf.WARRIORS.loc[21]
s_shangshanqianxin = conf.WARRIORS.loc[27]
s_demo = pd.Series([100, 100, 100, ""], index=["統率", "武勇", "智略", "類型戰鬥特性"])
s_opponent = pd.Series([100, 100, 100, ""], index=["統率", "武勇", "智略", "類型戰鬥特性"])


def init_log():
    return pd.DataFrame({
        "tik": [],
        "team_figures": [],
        "opponent_figures": [],
        "kills": [],
        "killed": [],
        "team_troops": [],
        "opponent_troops": [],
        "activated_traits": [],
        "team_attack_factor": [],
        "team_defense_factor": [],
        "team_damage_factor": [],
        "opponent_traits": [],
        "opponent_attack_factor": [],
        "opponent_defense_factor": [],
        "opponent_damage_factor": []
    })


def battle_log(log: pd.DataFrame, tik, team, opponent, kills, killed):
    row = {
        "tik": tik,
        "team_figures": (team.tong, team.wu, team.zhi),
        "opponent_figures": (opponent.tong, opponent.wu, opponent.zhi),
        "kills": kills,
        "killed": killed,
        "team_troops": team.troops,
        "opponent_troops": opponent.troops,
        "activated_traits": team.traits[team.traits["activated"]]["name"].values,
        "team_attack_factor": team.attack_factor,
        "team_defense_factor": team.defense_factor,
        "team_damage_factor": team.damage_factor,
        "opponent_attack_factor": opponent.attack_factor,
        "opponent_defense_factor": opponent.defense_factor,
        "opponent_damage_factor": opponent.damage_factor,
        "opponent_traits": opponent.traits[opponent.traits["activated"]]["name"].values
    }
    return log.append(row, ignore_index=True)


def test_battle():
    log = init_log()

    team = Team([s_wutianxinxuan], 10000)
    opponent = Team([s_shangshanqianxin], 10000)

    team.set_opponent(opponent)
    opponent.set_opponent(team)

    tik = 1
    while team.troops > 0 and opponent.troops > 0:
        team.update_traits_on_tik_start()
        opponent.update_traits_on_tik_start()
        if tik % 3 == 0:
            team.update_traits_on_battle_start()
            opponent.update_traits_on_battle_start()

            team.update_team_factors()
            opponent.update_team_factors()

            kills = team.calculate_kills()
            killed = opponent.calculate_kills()

            team.take_damage(killed)
            opponent.take_damage(kills)

            log = battle_log(log, tik, team, opponent, kills, killed)

            team.update_traits_on_battle_end()
            opponent.update_traits_on_battle_end()

        team.update_traits_on_tik_end()
        opponent.update_traits_on_tik_end()

        tik = tik + 1

    log.to_excel("battle_log.xlsx", index=False)

    assert True
