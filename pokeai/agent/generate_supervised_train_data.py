"""
教師あり学習のデータ生成

局面での期待値最大ダメージの技を選ぶデータを作成
"""

import os
import argparse
from typing import List, Tuple
import numpy as np
from bson import ObjectId
import copy
import random

from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_agents import load_agent
from pokeai.agent.common import match_agents
from pokeai.agent.util import save_pickle
from pokeai.sim import context
from pokeai.agent import party_db
from pokeai.sim.party_template import PartyTemplate

from pokeai.agent.battle_agent import BattleAgent
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.move_info_db import move_info_db
from pokeai.sim.move_learn_db import move_learn_db
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType


def calc_party_remain_rate_sep(party: Party):
    """
    パーティのHP残存率(0~1)、生存率(0~1)をそれぞれ計算
    :param party:
    :return: (HP残存率,生存率)
    """
    sum_remain_hp = 0.0
    sum_remain_life = 0.0
    for poke in party.pokes:
        sum_remain_hp += poke.hp / poke.max_hp
        sum_remain_life += int(not poke.is_faint())
    sum_remain_hp /= len(party.pokes)
    sum_remain_life /= len(party.pokes)
    return sum_remain_hp, sum_remain_life


def calc_party_remain_rate_sep_diff(field: Field):
    """
    calc_party_remain_rate_sepのパーティ間差分を計算。
    player 0が有利な時正の値となる。
    :param field:
    :return:
    """
    h0, l0 = calc_party_remain_rate_sep(field.parties[0])
    h1, l1 = calc_party_remain_rate_sep(field.parties[1])
    return h0 - h1, l0 - l1


def simulate_action(field: Field, actions: List[FieldAction]):
    assert field.phase is FieldPhase.BEGIN
    c_field = copy.deepcopy(field)

    rrh_before, rrl_before = calc_party_remain_rate_sep_diff(c_field)
    # 乱数を変化させる
    c_field.rng._rng.seed(random.randrange(0, 2 ** 31))
    c_field.actions_begin = actions
    c_field.step()
    rrh_after, rrl_after = calc_party_remain_rate_sep_diff(c_field)
    return rrh_after - rrh_before, rrl_after - rrl_before


def log_nop(x):
    pass


def get_action_str(field: Field, player: int, action: FieldAction):
    """
    actionの内容（技名・交代先）を表すデバッグ用文字列を出力
    :param field:
    :param player:
    :param action:
    :return:
    """
    poke = field.parties[player].get()
    if action.action_type is FieldActionType.MOVE:
        return "Move." + poke.moves[action.move_idx].move.name
    elif action.action_type is FieldActionType.CHANGE:
        return "Poke." + field.parties[player].get(action.change_idx).poke_static.dexno.name
    return "?"


def select_best_action(field: Field):
    legal_actions_list = [field.get_legal_actions(player) for player in range(2)]
    # player0からみたスコア表
    score_mat = np.zeros((len(legal_actions_list[0]), len(legal_actions_list[1])), dtype=np.float)
    # シミュレーション用にログ出力抑制
    log_bak = field.put_record
    field.put_record = log_nop
    n_simu = 10
    for i in range(len(legal_actions_list[0])):
        for j in range(len(legal_actions_list[1])):
            actions = [legal_actions_list[0][i], legal_actions_list[1][j]]
            for simu in range(n_simu):
                rrh, rrl = simulate_action(field, actions)
                score = rrh * 0.5 + rrl * 0.5
                score_mat[i, j] += score
    score_mat /= n_simu

    field.put_record = log_bak
    # 各プレイヤーからみて、期待値最大の行動をとる（相手はランダムに動くと仮定）
    best_actions = [
        legal_actions_list[0][np.argmax(np.mean(score_mat, axis=1))],
        legal_actions_list[1][np.argmin(np.mean(score_mat, axis=0))]
    ]

    if True:
        for player in range(2):
            field.put_record_other(f"Player{player}: {str(field.parties[player])}")
            exp_str = f"スコア期待値 Player{player}"
            exp_score = np.mean(score_mat, axis=1 - player)
            for i in range(len(legal_actions_list[player])):
                exp_str += f" {get_action_str(field, player, legal_actions_list[player][i])}={exp_score[i]}"
            field.put_record_other(exp_str)

    return best_actions


def select_first_action(field: Field):
    """
    アクションリストの最初の行動を選ぶ。瀕死交代用。
    :param field:
    :return:
    """
    actions = []
    for player in range(2):
        las = field.get_legal_actions(player)
        if len(las) > 0:
            actions.append(las[0])
        else:
            actions.append(None)
    return actions


def select_random_action(field: Field):
    """
    アクションリストからランダムに行動を選ぶ。
    :param field:
    :return:
    """
    actions = []
    for player in range(2):
        las = field.get_legal_actions(player)
        if len(las) > 0:
            actions.append(random.choice(las))
        else:
            actions.append(None)
    return actions


def run_battle(parties: List[PartyTemplate]):
    log_objs = []
    log_func = lambda record: log_objs.append(record)
    field = Field([parties[0].create(), parties[1].create()])
    field.rng = GameRNGRandom()
    field.rng.set_field(field)
    field.put_record = log_func

    winner = -1
    next_phase = FieldPhase.BEGIN
    while True:
        actions = []
        if next_phase is FieldPhase.BEGIN:
            field.actions_begin = select_best_action(field)
        elif next_phase is FieldPhase.FAINT_CHANGE:
            field.actions_faint_change = select_first_action(field)
        next_phase = field.step()
        if next_phase is FieldPhase.GAME_END:
            winner = field.winner
            break
        if field.turn_number >= 64:
            break
    return log_objs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("my_party", help="自分側パーティid")
    parser.add_argument("enemy_party_tag", help="敵として使うパーティグループのtag")
    # parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    parser.add_argument("--log", help="対戦ログの保存ディレクトリ")
    args = parser.parse_args()
    context.init()
    my_party = party_db.load_party_template(ObjectId(args.my_party))
    enemy_parties = party_db.load_party_group(args.enemy_party_tag)
    battle_log = run_battle([my_party, enemy_parties[0]])
    for entry in battle_log:
        print(entry)


if __name__ == '__main__':
    main()
