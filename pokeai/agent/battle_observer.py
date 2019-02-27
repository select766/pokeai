"""
バトルエージェントへの入力特徴生成・行動のオブジェクトへの変換
"""
import random
import gym
from typing import List, Optional, Iterable, Tuple, Dict
import numpy as np
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.party import Party
from pokeai.sim.poke import Poke, PokeNVCondition
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType


class BattleObserver:
    party_size: int  # 各プレイヤーの所持ポケモン数
    observation_space: gym.spaces.Box
    action_space: gym.spaces.Discrete
    feature_types: List[str]
    illegal_random: bool  # 無効なアクション番号を与えた場合ランダムな行動を選択。Falseなら有効なものの先頭。

    def __init__(self, party_size: int, feature_types: List[str], illegal_random: bool = False):
        self.party_size = party_size
        self.feature_types = feature_types
        self.action_space = gym.spaces.Discrete(
            6 * self.party_size)  # 技4つ*party_size+交代(通常交代、瀕死の交代)*party_size
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=self.get_observation_shape(), dtype=np.float32)
        self.illegal_random = illegal_random

    def get_config(self):
        return {"party_size": self.party_size, "feature_types": self.feature_types,
                "illegal_random": self.illegal_random}

    def get_field_action_map(self, field: Field, player: int) -> Dict[int, FieldAction]:
        """
        有効なアクションの番号とFieldActionオブジェクトを返す。
        :param field:
        :param player:
        :return:
        """
        player_possible_actions = field.get_legal_actions(player)
        fighting_idx = field.parties[player].fighting_idx
        action_map = {}  # 行動の番号からFieldActionへのマップ
        for ppa in player_possible_actions:
            if ppa.action_type is FieldActionType.MOVE:
                anum = ppa.move_idx + fighting_idx * 6
            elif ppa.action_type is FieldActionType.CHANGE:
                anum = ppa.change_idx * 6 + 4
            elif ppa.action_type is FieldActionType.FAINT_CHANGE:
                anum = ppa.faint_change_idx * 6 + 5
            else:
                raise NotImplementedError
            action_map[anum] = ppa
        return action_map

    def get_field_action(self, field: Field, player: int, action: int) -> Tuple[FieldAction, bool]:
        """
        行動番号からFieldActionオブジェクトに変換。
        無効な選択をしたら、self.illegal_randomに従って選択
        :param player:
        :param action: N番目のポケモンについて、選択する技(0+6N,1+6N,2+6N,3+6N)、このポケモンに交代(4+6N)、瀕死時にこのポケモンに交代(5+6N)
        :return:
        """
        assert 0 <= action < (6 * self.party_size)
        action_map = self.get_field_action_map(field, player)
        legal = True
        if action not in action_map:
            legal = False
            if self.illegal_random:
                action = random.choice(list(action_map.keys()))
            else:
                action = min(action_map.keys())
        player_action = action_map[action]
        return player_action, legal

    def get_observation_shape(self) -> Iterable[int]:
        dims = 0
        if "legal_action" in self.feature_types:
            dims += 6 * self.party_size
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
            dims += self.party_size
        if "alive_idx" in self.feature_types:
            dims += self.party_size
        return dims,

    def make_observation(self, field: Field, player: int) -> np.ndarray:
        """
        現在の局面を表すベクトルを生成する。値域0~1。
        player: 観測側プレイヤー。通常は0。
        :return:
        """
        parties = [field.parties[player], field.parties[1 - player]]
        pokes = [field.parties[player].get(), field.parties[1 - player].get()]  # 自分、相手
        pokests = [poke.poke_static for poke in pokes]

        feats = []
        if "legal_action" in self.feature_types:
            feats.append(self._obs_legal_actions(field, player))
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

    def _obs_legal_actions(self, field: Field, player: int) -> np.ndarray:
        feat = np.zeros(6 * self.party_size, dtype=np.float32)
        for action in self.get_field_action_map(field, player).keys():
            feat[action] = 1
        return feat

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
        feat = np.zeros(self.party_size, dtype=np.float32)
        feat[party.fighting_idx] = 1.0
        return feat

    def _obs_alive_idx(self, party: Party) -> np.ndarray:
        """
        瀕死でないポケモンのindex (場に出ているものを含む)
        :param party:
        :return:
        """
        feat = np.zeros(self.party_size, dtype=np.float32)
        for i in range(self.party_size):
            if not party.get(i).is_faint():
                feat[i] = 1.0
        return feat
