from typing import List

from pokeai.ai.battle_status import BattleStatus
import numpy as np
from pokeai.util import json_load, DATASET_DIR


class ChoiceToVec:
    """
    選択肢をベクトルに変換する特徴抽出器
    自分のポケモン、技のone-hot vector
    """

    def __init__(self):
        self.all_pokemons = json_load(DATASET_DIR.joinpath("all_pokemons.json"))
        self.pokemon_to_idx = {name: i for i, name in enumerate(self.all_pokemons)}
        self.all_moves = json_load(DATASET_DIR.joinpath("all_moves.json"))
        self.move_to_idx = {name: i + len(self.all_pokemons) for i, name in enumerate(self.all_moves)}

    def get_dims(self) -> int:
        """
        特徴次元数
        :return:
        """
        dims = len(self.all_pokemons) + len(self.all_moves)
        return dims

    def get_dim_meanings(self) -> List[str]:
        means = []
        means += [f"poke/{name}" for name in self.all_pokemons]
        means += [f"move/{name}" for name in self.all_moves]
        return means

    def transform(self, battle_status: BattleStatus, request: dict) -> np.ndarray:
        """
        特徴抽出
        :param battle_status:
        :param request:
        :return: 各選択肢（現状技0~3のみ）に対応する特徴量、(self.get_dims(), 4) float32
        """
        assert len(battle_status.side_party) == 1  # パーティ1体の時でないと使えない
        # FIXME: disabledな技の扱い
        poke = battle_status.side_party[0]["species"]
        moves = battle_status.side_party[0]["moves"]
        feat = np.zeros((self.get_dims(), 4), dtype=np.float32)  # convolutionにかけることを考えるとchannel, length
        feat[self.pokemon_to_idx[poke], :] = 1.0
        assert len(moves) == 4
        for i, move in enumerate(moves):
            feat[self.move_to_idx[move], i] = 1.0
        return feat
