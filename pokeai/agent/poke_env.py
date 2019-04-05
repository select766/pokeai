"""
OpenAI Gym互換のポケモンバトル環境

シミュレータをラップして強化学習フレームワークと接続する。
"""
from typing import List, Iterable, Optional, Callable, Tuple
import copy
import random
import numpy as np
import gym
from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_observer import BattleObserver

from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.move_info_db import move_info_db
from pokeai.sim.move_learn_db import move_learn_db
from pokeai.sim.party import Party
from pokeai.sim.party_template import PartyTemplate
from pokeai.sim.poke import Poke, PokeNVCondition
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType
from pokeai.sim import context


class RewardConfig:
    """
    勝敗以外の報酬設定
    """
    illegal_action: float
    damage: float
    faint: float

    def __init__(self, *, illegal_action: float = -0.1, damage: float = 0.5, faint: float = 0.5):
        self.illegal_action = illegal_action
        self.damage = damage
        self.faint = faint


class PokeEnv(gym.Env):
    """
    OpenAI Gym互換のポケモンバトル環境
    対戦の両プレイヤーをエージェントにして対戦させる機能も持つ。
    """
    player_party_t: PartyTemplate
    observer: BattleObserver
    enemy_agent: BattleAgent
    enemy_agents: List[BattleAgent]
    next_party_idxs: List[int]
    field: Field
    done: bool
    feature_types: List[str]
    party_size: int  # パーティのポケモン数
    reward_config: RewardConfig
    MAX_TURNS = 64

    def __init__(self, player_party_t: PartyTemplate, observer: BattleObserver, enemy_agents: List[BattleAgent],
                 reward_config: Optional[RewardConfig] = None):
        super().__init__()
        self.player_party_t = player_party_t
        self.observer = observer
        self.party_size = len(player_party_t.poke_sts)
        self.enemy_agents = enemy_agents
        self.next_party_idxs = []
        self.field = None
        self.enemy_agent = None
        self.done = True
        self.action_space = observer.action_space
        self.observation_space = observer.observation_space
        self.reward_range = (-1.0, 1.0)
        if reward_config is None:
            reward_config = RewardConfig()
        self.reward_config = reward_config

    def reset(self, enemy_agent: Optional[BattleAgent] = None):
        """
        敵パーティを選択し、フィールドを初期状態にする。
        :return:
        """
        self.enemy_agent = None
        if enemy_agent is None:
            if len(self.next_party_idxs) == 0:
                self.next_party_idxs = list(range(len(self.enemy_agents)))
                random.shuffle(self.next_party_idxs)
            enemy_party_idx = self.next_party_idxs.pop()
            self.enemy_agent = self.enemy_agents[enemy_party_idx]
        else:
            self.enemy_agent = enemy_agent
        self.field = Field([self.player_party_t.create(), self.enemy_agent.party_t.create()])
        self.field.put_record = lambda x: None
        self.done = False
        return self.observer.make_observation(self.field, 0)

    def step(self, action: int):
        """
        ターンを進める。
        :param action: 行動番号
        無効な選択をしたら、有効なものの中で先頭のものが選ばれる
        :return:
        """
        assert not self.done, "call reset before step"
        dr_before = self._calc_damage_reward()

        assert len(self.observer.get_field_action_map(self.field, 0)) > 0  # 合法手があるはず(敵側のみの交代要求ではない)
        player_action, legal = self.observer.get_field_action(self.field, 0, action)

        enemy_action = self.enemy_agent.get_action(self.field, 1)
        actions = [player_action, enemy_action]
        if self.field.phase is FieldPhase.BEGIN:
            self.field.actions_begin = actions
        elif self.field.phase is FieldPhase.FAINT_CHANGE:
            self.field.actions_faint_change = actions
        else:
            raise NotImplementedError
        phase = self.field.step()

        dr_after = self._calc_damage_reward()  # player0に有利なら大きな値になっている

        reward = dr_after - dr_before
        if not legal:  # illegal actionを選ばないようにするためにrewardでフィードバックする
            reward += self.reward_config.illegal_action
        if phase is FieldPhase.GAME_END:
            self.done = True
            reward += [1.0, -1.0][self.field.winner]
        else:
            if self.field.turn_number >= PokeEnv.MAX_TURNS:
                # 引き分けで打ち切り
                self.done = True
            if phase is FieldPhase.BEGIN:
                pass
            elif phase is FieldPhase.FAINT_CHANGE:
                # プレイヤー側のポケモンの交代が必要ならここでreturnして行動を取得、敵側のみならその行動を取得して進める
                self._faint_change_forward()
            else:
                raise NotImplementedError

        reward = max(min(reward, 1.0), -1.0)

        return self.observer.make_observation(self.field, 0), reward, self.done, {}

    def _faint_change_forward(self):
        """
        phaseがFieldPhase.FAINT_CHANGEのときに、プレイヤー側のポケモンの交代が必要ならreturnして行動を取得、敵側のみならその行動を取得して進める
        :return:
        """
        player_legals = self.field.get_legal_actions(0)
        if len(player_legals) > 0:
            # プレイヤー側の交代が必要
            return
        # 敵側のみ交代
        enemy_action = self.enemy_agent.get_action(self.field, 1)
        self.field.actions_faint_change = [None, enemy_action]
        assert self.field.step() == FieldPhase.BEGIN

    def _calc_damage_reward(self) -> float:
        """
        ダメージに対する報酬の計算。ターンの開始時と終了時の差がそのターンの報酬となる。
        :return: player0に有利なら正、不利なら負の値
        """
        rr_diff = self._calc_party_remain_rate(self.field.parties[0]) - self._calc_party_remain_rate(
            self.field.parties[1])
        return rr_diff * self.reward_config.damage

    def _calc_party_remain_rate(self, party: Party) -> float:
        """
        パーティのHP残存率の計算
        :param party:
        :return: 初期状態で1.0、すべて瀕死で0.0
        """
        sum_remain = 0.0
        rc = self.reward_config
        for poke in party.pokes:
            # 生きている: rc.faintを加算
            sum_remain += int(not poke.is_faint()) * rc.faint
            # 残っているHP率 * (1.0-rc.faint)を加算
            sum_remain += (poke.hp / poke.max_hp) * (1.0 - rc.faint)
        sum_remain /= len(party.pokes)
        return sum_remain
