"""
OpenAI Gym互換のポケモンバトル環境

シミュレータをラップして強化学習フレームワークと接続する。

現状の制限
- パーティのポケモンは1体のみ。交代のサポートなし。
- 敵パーティの行動はランダム。
"""
from typing import List, Iterable, Optional
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


class PokeEnv(gym.Env):
    """
    OpenAI Gym互換のポケモンバトル環境
    """
    player_party: Party
    enemy_parties: List[Party]
    next_party_idxs: List[int]
    field: Field
    done: bool
    feature_types: List[str]
    MAX_TURNS = 64

    def __init__(self, player_party: Party, enemy_parties: List[Party], feature_types: List[str]):
        super().__init__()
        self.player_party = player_party
        self.enemy_parties = enemy_parties
        self.next_party_idxs = []
        self.field = None
        self.done = True
        self.feature_types = feature_types
        self.action_space = gym.spaces.Discrete(4)  # 技4つ
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=self._get_observation_shape(), dtype=np.float32)
        self.reward_range = (-1.0, 1.0)

    def reset(self, enemy_party: Optional[Party]=None):
        """
        敵パーティを選択し、フィールドを初期状態にする。
        :return:
        """
        if enemy_party is None:
            if len(self.next_party_idxs) == 0:
                self.next_party_idxs = list(range(len(self.enemy_parties)))
                random.shuffle(self.next_party_idxs)
            enemy_party = self.enemy_parties[self.next_party_idxs.pop()]
        self.field = Field([copy.deepcopy(self.player_party), copy.deepcopy(enemy_party)])
        self.field.put_record = lambda x: None
        self.done = False
        return self._make_observation()

    def step(self, action: int):
        """
        ターンを進める。
        :param action: 選択する技(0,1,2,3)、技がN個ある場合、N以降を指定した場合は0と同等に扱われる
        :return:
        """
        assert not self.done, "call reset before step"
        assert 0 <= action <= 3
        player_possible_actions = self.field.get_legal_actions(0)
        move_idx = action
        # 指定した技が使えるならそれを選択、そうでなければ先頭の技
        # 連続技の最中は選択にかかわらず強制的に技が選ばれる
        player_action = player_possible_actions[0]
        for ppa in player_possible_actions:
            if ppa.action_type is FieldActionType.MOVE and ppa.move_idx == move_idx:
                player_action = ppa
                break
        enemy_action = random.choice(self.field.get_legal_actions(1))
        self.field.actions_begin = [player_action, enemy_action]
        phase = self.field.step()

        reward = 0.0
        if phase is FieldPhase.GAME_END:
            self.done = True
            reward = [1.0, -1.0][self.field.winner]
        else:
            if self.field.turn_number >= PokeEnv.MAX_TURNS:
                # 引き分けで打ち切り
                self.done = True
            if phase is FieldPhase.BEGIN:
                pass
            else:
                # 瀕死交代未実装
                raise NotImplementedError

        return self._make_observation(), reward, self.done, {}

    def _get_observation_shape(self) -> Iterable[int]:
        dims = 0
        if "enemy_dexno" in self.feature_types:
            dims += Dexno.MEW.value - Dexno.BULBASAUR.value + 1
        if "hp_ratio" in self.feature_types:
            dims += 1 * 2
        if "nv_condition" in self.feature_types:
            dims += 6 * 2
        if "rank" in self.feature_types:
            dims += 6 * 2
        return dims,

    def _make_observation(self) -> np.ndarray:
        """
        現在の局面を表すベクトルを生成する。値域0~1。
        :return:
        """
        pokes = [self.field.parties[i].get() for i in range(2)]
        pokests = [poke._poke_st for poke in pokes]

        feats = []
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
        return np.concatenate(feats)

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
