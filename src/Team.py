import numpy as np
import pandas as pd

import config as conf


class Team():

    def __init__(self, warriors: [pd.Series], troops: int):

        if not isinstance(warriors, list):
            warriors = [warriors]

        self.warriors = warriors
        self.troops = troops
        self.initial_troops = troops

        self.tong = warriors[0]["統率"]
        self.wu = warriors[0]["武勇"]
        self.zhi = warriors[0]["智略"]
        for warrior in warriors[1:]:
            self.wu = max(self.wu, warrior["武勇"] * min(self.tong / 100, 1))
            self.zhi = max(self.zhi, warrior["智略"] * min(self.tong / 100, 1))

        self.tong_lead = warriors[0]["統率"]
        self.wu_lead = warriors[0]["武勇"]
        self.zhi_lead = warriors[0]["智略"]

        self.traits = self.__collect_traits(warriors)

    def __collect_traits(self, warriors: [pd.Series]):
        traits_list = []
        for warrior in warriors:
            traits_list = traits_list + warrior["類型戰鬥特性"].split(",")
        traits_list = list(set(traits_list))

        return conf.TRAITS_DEFAULT[conf.TRAITS_DEFAULT["name"].isin(traits_list)]

    def set_opponent(self, opponent: "Team"):
        self.opponent = opponent

    def update_traits_on_tik_start(self):
        # 只取每天都能觸發的特性
        tik_traits = self.traits[~self.traits["activated_on_battle"]]
        for idx, warrior in enumerate(self.warriors):
            mask_deactivated_traits = ~tik_traits["activated"]
            mask_warrior_traits = tik_traits["name"].isin(warrior["類型戰鬥特性"].split(","))

            # 武將為 大將/副將 相關的特性
            mask_positional_traits = tik_traits["on_warrior_position"] == min(idx, 1)
            mask = mask_deactivated_traits & mask_warrior_traits & mask_positional_traits
            tik_traits.loc[mask, "activated"] = tik_traits[mask]["activation_rate"] \
                .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 兵力百分比的特性: 不屈
            mask_troops_traits = tik_traits["on_troops_percentage"] >= (self.troops / self.initial_troops)
            mask = mask_deactivated_traits & mask_warrior_traits & mask_troops_traits
            tik_traits.loc[mask, "activated"] = tik_traits[mask]["activation_rate"] \
                .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 其他特性
            mask_other_traits = ~mask_positional_traits
            mask = mask_deactivated_traits & mask_warrior_traits & mask_other_traits
            tik_traits.loc[mask, "activated"] = tik_traits[mask]["activation_rate"] \
                .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

        # 更新隊伍特性列表
        self.traits.loc[tik_traits.index, "activated"] = tik_traits["activated"].astype(bool)

    def update_traits_on_tik_end(self):
        # 所有生效特性有效期 - 1
        mask = self.traits["activated"]
        self.traits.loc[mask, "activated_until"] = self.traits[mask]["activated_until"] - 1

        # 重置有效期為 0 的特性
        traits_to_deactivate = self.traits[self.traits["activated_until"] == 0]
        traits_to_deactivate.loc[
            :, ["activated", "activated_until"]
        ] = conf.TRAITS_DEFAULT.loc[
            traits_to_deactivate.index, ["activated", "activated_until"]
        ]

        # 更新隊伍特性列表
        self.traits.loc[
            traits_to_deactivate.index, ["activated", "activated_until"]
        ] = traits_to_deactivate[["activated", "activated_until"]]

    def update_traits_on_battle_start(self):
        # 只取戰鬥時才觸發的特性
        battle_traits = self.traits[self.traits["activated_on_battle"]]
        for idx, warrior in enumerate(self.warriors):
            mask_deactivated_traits = ~battle_traits["activated"]
            mask_warrior_traits = battle_traits["name"].isin(warrior["類型戰鬥特性"].split(","))

            # 要求3人組隊的特性: 波狀攻擊
            mask_full_team_traits = battle_traits["on_full_team"]
            if len(self.warriors) == 3:
                mask = mask_deactivated_traits & mask_warrior_traits & mask_full_team_traits
                battle_traits.loc[mask, "activated"] = battle_traits[mask]["activation_rate"] \
                    .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 第一次攻擊的特性
            mask_first_strike_traits = battle_traits["on_first_strike"]
            mask = mask_deactivated_traits & mask_warrior_traits & mask_first_strike_traits
            battle_traits.loc[mask, "activated"] = battle_traits[mask]["activation_rate"] \
                .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 兵力多于对方
            mask_on_bigger_troops = battle_traits["on_bigger_troops"]
            if self.troops > self.opponent.troops:
                mask = mask_deactivated_traits & mask_warrior_traits & mask_on_bigger_troops
                battle_traits.loc[mask, "activated"] = battle_traits[mask]["activation_rate"] \
                    .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 兵力少于对方
            mask_on_smaller_troops = battle_traits["on_smaller_troops"]
            if self.troops < self.opponent.troops:
                mask = mask_deactivated_traits & mask_warrior_traits & mask_on_smaller_troops
                battle_traits.loc[mask, "activated"] = battle_traits[mask]["activation_rate"] \
                    .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 智略高于对方
            mask_on_higher_intelegence = battle_traits["on_higher_intelegence"]
            if self.zhi > self.opponent.zhi:
                mask = mask_deactivated_traits & mask_warrior_traits & mask_on_higher_intelegence
                battle_traits.loc[mask, "activated"] = battle_traits[mask]["activation_rate"] \
                    .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

            # 其他特性 + 兵力百分比的特性 + 大將/副將特性
            mask_requires_troops = battle_traits["on_troops_percentage"] >= 0
            mask_requires_position = battle_traits["on_warrior_position"] >= 0
            mask_other_traits = ~(
                mask_full_team_traits | mask_first_strike_traits | mask_on_bigger_troops | mask_on_smaller_troops |
                mask_on_higher_intelegence | mask_requires_troops | mask_requires_position
            )
            mask_troops_validated = battle_traits["on_troops_percentage"] >= (self.troops / self.initial_troops)
            mask_positios_validated = battle_traits["on_warrior_position"] == min(idx, 1)
            mask = (mask_deactivated_traits & mask_warrior_traits & mask_other_traits) | \
                mask_troops_validated | mask_positios_validated
            battle_traits.loc[mask, "activated"] = battle_traits[mask]["activation_rate"] \
                .apply(lambda x: np.random.choice([True, False], p=[x, 1 - x]))

        # 更新隊伍特性列表
        self.traits.loc[battle_traits.index, "activated"] = battle_traits["activated"].astype(bool)

    def update_traits_on_battle_end(self):
        mask_activated = self.traits["activated"]

        # 對所有生效的，有持續時間且非常駐的特性，移除 傷害增加，損害減小 效果
        mask_non_infty = self.traits["activated_until"] < np.infty
        mask_not_one_day = self.traits["activated_until"] > 1
        mask = mask_activated & mask_non_infty & mask_not_one_day
        self.traits.loc[mask, ["damage_increase", "loss_decrease"]] = [0, 0]

        # 移除所有已觸發的第一次攻擊觸發的特性，
        mask_first_strike = self.traits["on_first_strike"]
        mask = mask_activated & mask_first_strike
        self.traits.drop(index=self.traits.loc[mask].index, inplace=True)

    def update_team_factors(self):
        # 更新隊伍攻防能力
        self.attack_factor = self.wu + self.traits[self.traits["activated"]]["attack_increase"].sum()
        self.attack_factor = self.attack_factor - \
            self.opponent.traits[self.opponent.traits["activated"]]["opponent_attack_decrease"].sum()
        self.defense_factor = self.tong + self.traits[self.traits["activated"]]["defense_increase"].sum()

    def _calculate_factor_A(self):
        if self.wu <= self.opponent.tong:
            return 0
        if self.wu > self.opponent.tong:
            return 10 + (self.wu - self.opponent.tong) / 2

    def _calculate_factor_B(self, A: float):
        x = (A + self.attack_factor) / self.opponent.defense_factor
        B = (x**2 + x) / 2

        B = min(B, 2)
        B = max(B, 0.25)

        return B

    def _calculate_basic_damage(self):
        x = self.troops + self.opponent.troops
        return x * 240 / 10000 + 148

    def _calculate_damage_factor(self):
        d_increase = self.traits[self.traits["activated"]]["damage_increase"].sum()
        d_decrease = self.opponent.traits[self.opponent.traits["activated"]]["opponent_damage_decrease"].sum() + \
            self.opponent.traits[self.opponent.traits["activated"]]["loss_decrease"].sum()
        self.damage_factor = max(1 + (d_increase - d_decrease) / 100, 0)
        return self.damage_factor

    def _calculate_horse_gun_factor(self):
        #  0.333 * 1 + 0.667 * 1.3
        return 1.2001

    def calculate_kills(self):
        A = self._calculate_factor_A()
        B = self._calculate_factor_B(A)
        b_damage = self._calculate_basic_damage()
        damage = (b_damage - 100) * B + 100
        damage = damage * self._calculate_damage_factor() * self._calculate_horse_gun_factor()
        return round(damage)

    def take_damage(self, killed):
        self.troops = self.troops - killed
        self.troops = max(self.troops, 0)
