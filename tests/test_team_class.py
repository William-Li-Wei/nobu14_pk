import pandas as pd
import numpy as np

from src.Team import Team
import config as conf


s_zhentianchangxing = conf.WARRIORS.loc[25]
s_zhentianxingcun = conf.WARRIORS.loc[26]
s_opponent1 = pd.Series([90, 90, 90, ""], index=["統率", "武勇", "智略", "類型戰鬥特性"])
s_opponent2 = pd.Series([100, 100, 100, ""], index=["統率", "武勇", "智略", "類型戰鬥特性"])


def test_team_inits_with_1_warrior():

    team = Team(s_zhentianxingcun, 10000)

    assert len(team.warriors) == 1
    assert team.troops == 10000

    assert team.tong == 92
    assert team.wu == 99
    assert team.zhi == 82

    assert team.tong_lead == 92
    assert team.wu_lead == 99
    assert team.zhi_lead == 82
    assert team.traits.empty is False


def test_team_inits_with_multiple_warriors():

    team = Team([s_zhentianxingcun, s_zhentianchangxing], 10000)

    assert len(team.warriors) == 2
    assert team.troops == 10000

    assert team.tong == 92
    assert team.wu == 99
    np.testing.assert_almost_equal(team.zhi, 90.16)

    assert team.tong_lead == 92
    assert team.wu_lead == 99
    assert team.zhi_lead == 82

    assert team.traits.empty is False


def test_team_collects_warriors_traits():
    s_warrior1 = pd.Series([90, 90, 90, "衝鋒,槍衾"], index=["統率", "武勇", "智略", "類型戰鬥特性"])
    s_warrior2 = pd.Series([90, 90, 90, "槍衾,名將"], index=["統率", "武勇", "智略", "類型戰鬥特性"])
    expected = conf.TRAITS_DEFAULT[conf.TRAITS_DEFAULT["name"].isin(["衝鋒", "槍衾", "名將"])]

    team = Team([s_warrior1, s_warrior2], 10000)

    assert pd.DataFrame.equals(team.traits, expected)


def test_team_updates_traits_on_tik_start():
    s_warrior = pd.Series(
        [90, 90, 90, "衝鋒,名將,氣勢,才貌雙全,不屈"],
        index=["統率", "武勇", "智略", "類型戰鬥特性"]
    )
    team = Team(s_warrior, 10000)
    team.traits.loc[:, "activation_rate"] = 1.0

    expected = team.traits.copy()
    expected.loc[expected["name"].isin(["名將", "才貌雙全", "不屈"]), "activated"] = True

    team.update_traits_on_tik_start()

    assert pd.DataFrame.equals(team.traits, expected)


def test_team_updates_traits_on_tik_end():
    s_warrior = pd.Series(
        [90, 90, 90, "衝鋒,名將,氣勢,才貌雙全,不屈"],
        index=["統率", "武勇", "智略", "類型戰鬥特性"]
    )
    team = Team(s_warrior, 10000)
    team.traits.loc[
        team.traits["name"].isin(["名將", "才貌雙全", "不屈"]),
        ["activated", "activated_until"]
    ] = [True, 1]
    team.traits.loc[
        team.traits["name"].isin(["不屈"]),
        ["activated", "activated_until"]
    ] = [True, 9]

    expected = team.traits.copy()
    expected.loc[
        expected["name"].isin(["名將", "才貌雙全", "不屈"]),
        ["activated", "activated_until"]
    ] = [False, 10]
    expected.loc[
        expected["name"].isin(["不屈"]),
        ["activated", "activated_until"]
    ] = [True, 8]

    team.update_traits_on_tik_end()

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    print(team.traits)
    print(expected)
    print(team.traits.dtypes)
    print(expected.dtypes)

    assert pd.DataFrame.equals(team.traits, expected)


def test_team_updates_traits_on_battle_start():
    s_warrior = pd.Series(
        [90, 90, 90, "衝鋒,先驅,氣勢,副將,波狀攻擊,名將"],
        index=["統率", "武勇", "智略", "類型戰鬥特性"]
    )
    team = Team(s_warrior, 10000)
    opponent = Team(s_opponent1, 10000)
    team.set_opponent(opponent)
    team.traits.loc[:, "activation_rate"] = 1.0

    expected = team.traits.copy()
    expected.loc[expected["name"].isin(["衝鋒", "先驅"]), "activated"] = True

    team.update_traits_on_battle_start()
    print(team.traits)
    print(expected)
    print(team.traits.dtypes)
    print(expected.dtypes)

    assert pd.DataFrame.equals(team.traits, expected)


def test_team_updates_traits_on_battle_end():
    s_warrior = pd.Series(
        [90, 90, 90, "衝鋒,先驅,氣勢,副將,波狀攻擊,名將,風林火山"],
        index=["統率", "武勇", "智略", "類型戰鬥特性"]
    )
    team = Team(s_warrior, 10000)
    team.traits.loc[:, "activated"] = True

    expected = team.traits.copy()
    expected.loc[
        expected["name"].isin(["氣勢", "風林火山"]),
        ["damage_increase", "loss_decrease"]
    ] = [0, 0]
    expected.drop(
        index=expected.loc[expected["name"] == "先驅"].index,
        inplace=True
    )

    team.update_traits_on_battle_end()

    assert pd.DataFrame.equals(team.traits, expected)
