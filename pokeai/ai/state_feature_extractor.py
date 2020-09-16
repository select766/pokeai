from typing import List, Optional

import numpy as np

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.dex import dex

POKE_TYPES = [
    "Normal",
    "Fighting",
    "Flying",
    "Poison",
    "Ground",
    "Rock",
    "Bug",
    "Ghost",
    "Steel",
    "Fire",
    "Water",
    "Grass",
    "Electric",
    "Psychic",
    "Ice",
    "Dragon",
    "Dark"
]

POKE_TYPE2NUM = {t: i for i, t in enumerate(POKE_TYPES)}

NV_CONDITIONS = ["psn", "tox", "par", "brn", "slp", "frz"]
RANKS = ['atk', 'def', 'spa', 'spd', 'spe', 'accuracy', 'evasion']
WEATHERS = ["SunnyDay", "RainDance", "Sandstorm"]


class StateFeatureExtractor:
    """
    バトルの状態を実数値ベクトルの特徴量に変換する
    """
    feature_types: List[str]
    party_size: int
    ALL_FEATURE_TYPES = [
        "remaining_count",
        "poke_type",
        "hp_ratio",
        "nv_condition",
        "rank",
        "weather"]
    # TODO: 持ち物があるかどうか（BattleStatusに現状情報がなく、requestから取り出す経路が必要）

    def __init__(self, feature_types: Optional[List[str]] = None, party_size: int = 3):
        self.feature_types = feature_types or StateFeatureExtractor.ALL_FEATURE_TYPES
        self.party_size = party_size

    def get_dims(self) -> int:
        """
        特徴次元数
        :return:
        """
        dims = 0
        if "remaining_count" in self.feature_types:
            dims += 2
        if "poke_type" in self.feature_types:
            dims += len(POKE_TYPES)  # 17
        if "hp_ratio" in self.feature_types:
            dims += 1 * 2
        if "nv_condition" in self.feature_types:
            dims += len(NV_CONDITIONS) * 2
        if "rank" in self.feature_types:
            dims += len(RANKS) * 2
        if "weather" in self.feature_types:
            dims += len(WEATHERS)
        return dims

    def get_dim_meanings(self) -> List[str]:
        ms = []  # type:List[str]
        if "remaining_count" in self.feature_types:
            ms += ["remaining_count/friend", "remaining_count/opponent"]
        if "poke_type" in self.feature_types:
            ms += [f"poke_type/opponent/{poke_type}" for poke_type in POKE_TYPES]
        if "hp_ratio" in self.feature_types:
            ms += ["hp_ratio/friend", "hp_ratio/opponent"]
        if "nv_condition" in self.feature_types:
            for side in ["friend", "opponent"]:
                ms += [f"nv_condition/{side}/{cond}" for cond in NV_CONDITIONS]
        if "rank" in self.feature_types:
            for side in ["friend", "opponent"]:
                ms += [f"rank/{side}/{rank}" for rank in RANKS]
        if "weather" in self.feature_types:
            ms += [f"weather/{weather}" for weather in WEATHERS]
        return ms

    def transform(self, battle_status: BattleStatus, choice_vec: np.ndarray) -> np.ndarray:
        feats = []
        if "remaining_count" in self.feature_types:
            feats.append(self._transform_remaining_count(battle_status, battle_status.side_friend))
            feats.append(self._transform_remaining_count(battle_status, battle_status.side_opponent))
        if "poke_type" in self.feature_types:
            feats.append(self._transform_poke_type(battle_status, battle_status.side_opponent))
        if "hp_ratio" in self.feature_types:
            feats.append(self._transform_hp_ratio(battle_status, battle_status.side_friend))
            feats.append(self._transform_hp_ratio(battle_status, battle_status.side_opponent))
        if "nv_condition" in self.feature_types:
            feats.append(self._transform_nv_condition(battle_status, battle_status.side_friend))
            feats.append(self._transform_nv_condition(battle_status, battle_status.side_opponent))
        if "rank" in self.feature_types:
            feats.append(self._transform_rank(battle_status, battle_status.side_friend))
            feats.append(self._transform_rank(battle_status, battle_status.side_opponent))
        if "weather" in self.feature_types:
            feats.append(self._transform_weather(battle_status, battle_status.side_friend))
        return np.concatenate(feats)

    def _transform_remaining_count(self, battle_status: BattleStatus, side: str) -> np.ndarray:
        """
        ポケモンの残り数/パーティサイズ
        :param battle_status:
        :param side:
        :return:
        """
        side_status = battle_status.side_statuses[side]
        feat = np.zeros((1,), dtype=np.float32)
        feat[0] = side_status.remaining_pokes / side_status.total_pokes
        return feat

    def _transform_poke_type(self, battle_status: BattleStatus, side: str) -> np.ndarray:
        """
        相手のタイプを表すベクトル
        :param battle_status:
        :param side:
        :return:
        """
        active = battle_status.side_statuses[side].active
        assert active is not None
        dex_poke_info = dex.get_pokedex_by_name(active.species)
        feat = np.zeros((len(POKE_TYPES),), dtype=np.float32)
        for poke_type in dex_poke_info["types"]:
            feat[POKE_TYPE2NUM[poke_type]] = 1.0
        return feat

    def _transform_hp_ratio(self, battle_status: BattleStatus, side: str) -> np.ndarray:
        """
        ポケモンの残りHP/最大HP
        :param battle_status:
        :param side:
        :return:
        """
        active = battle_status.side_statuses[side].active
        assert active is not None
        feat = np.zeros((1,), dtype=np.float32)
        feat[0] = active.hp_current / active.hp_max
        return feat

    def _transform_nv_condition(self, battle_status: BattleStatus, side: str) -> np.ndarray:
        """
        状態異常
        :param battle_status:
        :param side:
        :return:
        """
        active = battle_status.side_statuses[side].active
        assert active is not None
        feat = np.zeros((len(NV_CONDITIONS),), dtype=np.float32)
        for i, cond in enumerate(NV_CONDITIONS):
            if cond == active.status:
                feat[i] = 1.0
                break
        return feat

    def _transform_rank(self, battle_status: BattleStatus, side: str) -> np.ndarray:
        """
        ランク補正
        :param battle_status:
        :param side:
        :return:
        """
        active = battle_status.side_statuses[side].active
        assert active is not None
        feat = np.zeros((len(RANKS),), dtype=np.float32)
        for i, cond in enumerate(RANKS):
            rank = active.ranks[cond]
            feat[i] = (rank + 6.0) / 12.0  # 0~1
        return feat

    def _transform_weather(self, battle_status: BattleStatus, side: str) -> np.ndarray:
        """
        天候
        :param battle_status:
        :param side:
        :return:
        """
        weather = battle_status.weather
        feat = np.zeros((len(WEATHERS),), dtype=np.float32)
        for i, w in enumerate(WEATHERS):
            if w == weather:
                feat[i] = 1.0
                break
        return feat
