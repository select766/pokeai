"""
OpenAI Gym互換のポケモンバトル環境

シミュレータをラップして強化学習フレームワークと接続する。

現状の制限
- パーティのポケモンは1体のみ。交代のサポートなし。
- 敵パーティの行動はランダム。
"""
from typing import List, Iterable, Optional, Callable, Tuple
import copy
import random
import numpy as np
import gym

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.move_info_db import move_info_db
from pokeai.sim.move_learn_db import move_learn_db
from pokeai.sim.party import Party
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
    player_party: Party
    enemy_parties: List[Party]
    enemy_agents: Optional[List[Callable[[np.ndarray], int]]]  # enemy_partiesの各要素に対応するエージェント
    next_party_idxs: List[int]
    field: Field
    done: bool
    feature_types: List[str]
    player_party_size: int  # プレイヤーのパーティのポケモン数
    random_change_rate: float  # ランダムに行動する場合に、交代を選ぶ確率
    reward_config: RewardConfig
    MAX_TURNS = 64

    def __init__(self, player_party: Party, enemy_parties: List[Party], feature_types: List[str],
                 random_change_rate=0.1, enemy_agents: Optional[List[Callable[[np.ndarray], int]]] = None,
                 reward_config: Optional[RewardConfig] = None):
        super().__init__()
        self.player_party = player_party
        self.player_party_size = len(player_party.pokes)
        self.enemy_parties = enemy_parties
        self.enemy_agents = enemy_agents
        self.next_party_idxs = []
        self.field = None
        self.enemy_agent = None
        self.done = True
        self.feature_types = feature_types
        self.action_space = gym.spaces.Discrete(
            5 * self.player_party_size)  # 技4つ*player_party_size+交代*player_party_size
        self.random_change_rate = random_change_rate
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=self._get_observation_shape(), dtype=np.float32)
        self.reward_range = (-1.0, 1.0)
        if reward_config is None:
            reward_config = RewardConfig()
        self.reward_config = reward_config

    def reset(self, enemy_party: Optional[Party] = None, enemy_agent: Optional[Callable[[np.ndarray], int]] = None):
        """
        敵パーティを選択し、フィールドを初期状態にする。
        :return:
        """
        self.enemy_agent = None
        if enemy_party is None:
            if len(self.next_party_idxs) == 0:
                self.next_party_idxs = list(range(len(self.enemy_parties)))
                random.shuffle(self.next_party_idxs)
            enemy_party_idx = self.next_party_idxs.pop()
            enemy_party = self.enemy_parties[enemy_party_idx]
            if self.enemy_agents is not None:
                # 敵パーティを動かすエージェント(Noneならランダム行動)
                self.enemy_agent = self.enemy_agents[enemy_party_idx]
        else:
            if enemy_agent is not None:
                self.enemy_agent = enemy_agent
        self.field = Field([copy.deepcopy(self.player_party), copy.deepcopy(enemy_party)])
        self.field.put_record = lambda x: None
        self.done = False
        return self._make_observation()

    def step(self, action: int):
        """
        ターンを進める。
        :param action: 選択する技(0,1,2,3)、交代(4,5,...) 交代は代わりに出すポケモンのパーティ上のインデックス+4
        無効な選択をしたら、有効なものの中で先頭のものが選ばれる
        :return:
        """
        assert not self.done, "call reset before step"
        dr_before = self._calc_damage_reward()
        player_action, legal = self._get_field_action(0, action)
        if self.enemy_agent is not None:
            obs = self._make_observation(1)
            action_num = self.enemy_agent(obs)
            enemy_action, _ = self._get_field_action(1, action_num)
        else:
            enemy_action = self._get_field_action_random(1)
        self.field.actions_begin = [player_action, enemy_action]
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
                # 瀕死交代は生きているポケモンの先頭
                self._faint_change_forward()
            else:
                raise NotImplementedError

        reward = max(min(reward, 1.0), -1.0)

        return self._make_observation(), reward, self.done, {}

    def _get_field_action(self, player: int, action: int) -> Tuple[FieldAction, bool]:
        """
        行動番号からFieldActionオブジェクトに変換。
        無効な選択をしたら、有効なものの中で先頭のものが選ばれる
        :param player:
        :param action: N番目のポケモンについて、選択する技(0+5N,1+5N,2+5N,3+5N)、このポケモンに交代(4+5N)
        :return:
        """
        assert 0 <= action < (5 * self.player_party_size)
        player_possible_actions = self.field.get_legal_actions(player)
        fighting_idx = self.field.parties[player].fighting_idx
        action_map = {}  # 行動の番号からFieldActionへのマップ
        for ppa in player_possible_actions:
            if ppa.action_type is FieldActionType.MOVE:
                anum = ppa.move_idx + fighting_idx * 5
            elif ppa.action_type is FieldActionType.CHANGE:
                anum = ppa.change_idx * 5 + 4
            else:
                raise NotImplementedError
            action_map[anum] = ppa
        legal = True
        if action not in action_map:
            legal = False
            action = min(action_map.keys())
            # action = random.choice(list(action_map.keys()))
        player_action = action_map[action]
        return player_action, legal

    def _get_field_action_random(self, player: int) -> FieldAction:
        """
        有効な行動からランダムにFieldActionオブジェクトを選択。
        :param player:
        :return:
        """
        player_possible_actions = self.field.get_legal_actions(player)
        actions_move = []
        actions_change = []
        for ppa in player_possible_actions:
            if ppa.action_type is FieldActionType.MOVE:
                actions_move.append(ppa)
            elif ppa.action_type is FieldActionType.CHANGE:
                actions_change.append(ppa)
            else:
                raise NotImplementedError
        if len(actions_move) > 0:
            if len(actions_change) > 0:
                # 技と交代の選択比率からどちらにするかランダムに決める
                if random.random() < self.random_change_rate:
                    actions = actions_change
                else:
                    # random_change_rateを0に設定すれば確実にこちらが選ばれる
                    actions = actions_move
            else:
                actions = actions_move
        else:
            assert len(actions_change) > 0
            actions = actions_change
        player_action = random.choice(actions)
        return player_action

    def _faint_change_forward(self):
        """
        phaseがFieldPhase.FAINT_CHANGEのときに、2プレイヤーの瀕死交代先を先頭の瀕死でないポケモンに選んで進める
        :return:
        """
        acts = []
        for player in range(2):
            legals = self.field.get_legal_actions(player)
            if len(legals) > 0:
                acts.append(legals[0])
            else:
                acts.append(None)
        self.field.actions_faint_change = acts
        assert self.field.step() == FieldPhase.BEGIN

    def match_agents(self, parties: List[Party], action_samplers: List[Optional[Callable[[np.ndarray], int]]],
                     put_record_func=None) -> int:
        """
        エージェント同士を対戦させる。
        :param parties: 対戦するパーティのリスト。内部でdeepcopyされる。
        :param action_samplers: observation vectorを受け取りactionを返す関数のリスト(要素がNoneならランダムに行動)
        :return: 勝ったパーティの番号(0 or 1)。引き分けなら-1。
        """
        self.field = Field([copy.deepcopy(p) for p in parties])
        if put_record_func is None:
            put_record_func = lambda x: None
        self.field.put_record = put_record_func
        while True:
            # 行動の選択
            actions_begin = []
            for player in range(2):
                obs = self._make_observation(player)
                if action_samplers[player] is not None:
                    action_num = action_samplers[player](obs)
                    action, _ = self._get_field_action(player, action_num)
                else:
                    action = self._get_field_action_random(player)
                actions_begin.append(action)
            self.field.actions_begin = actions_begin
            phase = self.field.step()

            if phase is FieldPhase.GAME_END:
                return self.field.winner
            else:
                if self.field.turn_number >= PokeEnv.MAX_TURNS:
                    # 引き分けで打ち切り
                    return -1
                if phase is FieldPhase.BEGIN:
                    pass
                elif phase is FieldPhase.FAINT_CHANGE:
                    # 瀕死交代は生きているポケモンの先頭
                    self._faint_change_forward()
                else:
                    raise NotImplementedError

    def _get_observation_shape(self) -> Iterable[int]:
        dims = 0
        if "enemy_type" in self.feature_types:
            dims += PokeType.DRAGON.value - PokeType.NORMAL.value + 1
        if "enemy_dexno" in self.feature_types:
            dims += Dexno.MEW.value - Dexno.BULBASAUR.value + 1
        if "hp_ratio" in self.feature_types:
            dims += 1 * 2
        if "nv_condition" in self.feature_types:
            dims += 6 * 2
        if "rank" in self.feature_types:
            dims += 6 * 2
        if "fighting_idx" in self.feature_types:
            dims += self.player_party_size
        if "alive_idx" in self.feature_types:
            dims += self.player_party_size
        return dims,

    def _make_observation(self, player: int = 0) -> np.ndarray:
        """
        現在の局面を表すベクトルを生成する。値域0~1。
        player: 観測側プレイヤー。通常は0。
        :return:
        """
        parties = [self.field.parties[player], self.field.parties[1 - player]]
        pokes = [self.field.parties[player].get(), self.field.parties[1 - player].get()]  # 自分、相手
        pokests = [poke.poke_static for poke in pokes]

        feats = []
        if "enemy_type" in self.feature_types:
            feats.append(self._obs_type(pokes[1]))
        if "enemy_dexno" in self.feature_types:
            feats.append(self._obs_dexno(pokests[1]))
        if "hp_ratio" in self.feature_types:
            feats.append(self._obs_hp_ratio(pokes[0]))
            feats.append(self._obs_hp_ratio(pokes[1]))
        if "nv_condition" in self.feature_types:
            feats.append(self._obs_nv_condition(pokes[0]))
            feats.append(self._obs_nv_condition(pokes[1]))
        if "rank" in self.feature_types:
            feats.append(self._obs_rank(pokes[0]))
            feats.append(self._obs_rank(pokes[1]))
        if "fighting_idx" in self.feature_types:
            # 相手パーティの情報は与えてないため、相手のindexは使いようがないはず
            feats.append(self._obs_fighting_idx(parties[0]))
        if "alive_idx" in self.feature_types:
            feats.append(self._obs_alive_idx(parties[0]))
        return np.concatenate(feats)

    def _obs_type(self, poke: Poke) -> np.ndarray:
        """
        タイプ(所持しているタイプの次元が1)
        :param poke:
        :return:
        """
        feat = np.zeros(PokeType.DRAGON.value - PokeType.NORMAL.value + 1, dtype=np.float32)
        for t in poke.poke_types:
            feat[t.value - PokeType.NORMAL.value] = 1
        return feat

    def _obs_dexno(self, pokest: PokeStatic) -> np.ndarray:
        """
        図鑑番号(one-hot)
        :param pokest:
        :return:
        """
        feat = np.zeros(Dexno.MEW.value - Dexno.BULBASAUR.value + 1, dtype=np.float32)
        feat[pokest.dexno.value - Dexno.BULBASAUR.value] = 1
        return feat

    def _obs_hp_ratio(self, poke: Poke) -> np.ndarray:
        """
        # 体力割合(満タンが1、ひんしが0)
        :param poke:
        :return:
        """
        feat = np.zeros(1, dtype=np.float32)
        feat[0] = poke.hp / poke.max_hp
        return feat

    def _obs_nv_condition(self, poke: Poke) -> np.ndarray:
        """
        状態異常(one-hot)
        :param poke:
        :return:
        """
        feat = np.zeros(PokeNVCondition.FREEZE.value - PokeNVCondition.EMPTY.value + 1, dtype=np.float32)
        feat[poke.nv_condition.value - PokeNVCondition.EMPTY.value] = 1
        return feat

    def _obs_rank(self, poke: Poke) -> np.ndarray:
        """
        ランク補正(-6~6を0~1に線形変換)
        :param poke:
        :return:
        """
        feat = np.zeros(6, dtype=np.float32)
        for i, rank in enumerate(
                [poke.rank_a, poke.rank_b, poke.rank_c, poke.rank_s, poke.rank_evasion, poke.rank_accuracy]):
            feat[i] = (rank.value + 6) / 12.0
        return feat

    def _obs_fighting_idx(self, party: Party) -> np.ndarray:
        """
        場に出ているポケモンのindex
        :param party:
        :return:
        """
        feat = np.zeros(self.player_party_size, dtype=np.float32)
        feat[party.fighting_idx] = 1.0
        return feat

    def _obs_alive_idx(self, party: Party) -> np.ndarray:
        """
        瀕死でないポケモンのindex (場に出ているものを含む)
        :param party:
        :return:
        """
        feat = np.zeros(self.player_party_size, dtype=np.float32)
        for i in range(self.player_party_size):
            if not party.get(i).is_faint():
                feat[i] = 1.0
        return feat

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
