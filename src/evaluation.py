import datetime
import pandas as pd
import numpy as np

from src.Team import Team

df_candidates = pd.read_excel("candidates.xlsx")
s_opponent = pd.Series([100, 100, 100, ""], index=["統率", "武勇", "智略", "類型戰鬥特性"])


def init_log():
    return pd.DataFrame({
        "candidate": [],
        "score": [],
        "team_figures": [],
        "opponent_figures": [],
        "battle": [],
        "tik": [],
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


def battle_log(log: pd.DataFrame, battle, tik, team, opponent, kills, killed, msg):
    score = np.nan
    if opponent.troops == 0:
        score = team.troops
    if team.troops == 0:
        score = - opponent.troops

    candidate = ",".join([w["名稱"] for w in team.warriors])

    row = {
        "candidate": candidate,
        "score": score,
        "team_figures": (team.tong, team.wu, team.zhi),
        "opponent_figures": (opponent.tong, opponent.wu, opponent.zhi),
        "battle": [],
        "tik": tik,
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
    if score is not np.nan:
        print(f"{datetime.datetime.now()}: battle {battle} of candidate {candidate}, score is {score}, #{msg}")
    return log.append(row, ignore_index=True)


def run_evaluation():
    log = init_log()
    total = df_candidates.shape[0]

    for idx, candidate in df_candidates.iterrows():
        idx = idx + 1
        msg = f"{idx}/{total}"
        for battle in range(1, 101):
            team = Team([candidate], 5000)
            opponent = Team([s_opponent], 5000)
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

                    log = battle_log(log, battle, tik, team, opponent, kills, killed, msg)

                    team.update_traits_on_battle_end()
                    opponent.update_traits_on_battle_end()

                team.update_traits_on_tik_end()
                opponent.update_traits_on_tik_end()

                tik = tik + 1

            log.to_excel("battle_log.xlsx", index=False)


if __name__ == "__main__":
    run_evaluation()
