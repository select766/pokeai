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


class FeatureExtractor:
    """
    バトルの状態を実数値ベクトルの特徴量に変換する
    """

    def __init__(self):
        pass

    def get_dims(self) -> int:
        """
        特徴次元数
        :return:
        """
        return len(POKE_TYPES)  # 17

    def transform(self, battle_status: BattleStatus) -> np.ndarray:
        return self._transform_type(battle_status)

    def _transform_type(self, battle_status: BattleStatus) -> np.ndarray:
        """
        相手のタイプを表すベクトル
        :param battle_status:
        :return:
        """
        active = battle_status.side_statuses[battle_status.side_opponent].active
        assert active is not None
        dex_poke_info = dex.get_pokedex_by_name(active.species)
        feat = np.zeros((len(POKE_TYPES),), dtype=np.float)
        for poke_type in dex_poke_info["types"]:
            feat[POKE_TYPE2NUM[poke_type]] = 1.0
        return feat
