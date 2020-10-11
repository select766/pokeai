from typing import List

from pokeai.ai.battle_status import BattleStatus
import numpy as np

from pokeai.ai.rl_policy_observation import RLPolicyObservation
from pokeai.util import json_load, DATASET_DIR


class ChoiceToVec:
    """
    選択肢をベクトルに変換する特徴抽出器
    自分のポケモン、技のone-hot vector
    """

    def __init__(self):
        dims = ["switch", "force_switch"]
        self.all_pokemons = json_load(DATASET_DIR.joinpath("all_pokemons.json"))
        self.pokemon_to_idx = {name: i + len(dims) for i, name in enumerate(self.all_pokemons)}
        dims += [f"poke/{name}" for name in self.all_pokemons]
        self.all_moves = json_load(DATASET_DIR.joinpath("all_moves_with_hiddenpower_type.json"))
        self.move_to_idx = {name: i + len(dims) for i, name in enumerate(self.all_moves)}
        dims += [f"move/{name}" for name in self.all_moves]
        self.all_items = json_load(DATASET_DIR.joinpath("all_items.json"))
        self.item_to_idx = {name: i + len(dims) for i, name in enumerate(self.all_items)}
        dims += [f"item/{name}" for name in self.all_items]
        self.dims = dims
        self.name_to_dim = {k: idx for idx, k in enumerate(dims)}

    def get_dims(self) -> int:
        """
        特徴次元数
        :return:
        """
        return len(self.dims)

    def get_dim_meanings(self) -> List[str]:
        return self.dims

    def transform(self, obs: RLPolicyObservation) -> np.ndarray:
        """
        特徴抽出
        :return: 各選択肢に対応する特徴量、(self.get_dims(), len(obs.possible_actions)) float32
        """
        feat = np.zeros((self.get_dims(), len(obs.possible_actions)),
                        dtype=np.float32)  # convolutionにかけることを考えるとchannel, length
        n2d = self.name_to_dim
        for a_idx, possible_action in enumerate(obs.possible_actions):
            if possible_action.force_switch:
                feat[n2d["force_switch"], a_idx] = 1
            if possible_action.switch:
                # force_switchのときも該当
                feat[n2d["switch"], a_idx] = 1
            feat[n2d["poke/" + possible_action.poke], a_idx] = 1
            if possible_action.switch:
                for move in possible_action.allMoves:
                    feat[n2d["move/" + move], a_idx] = 1
            else:
                feat[n2d["move/" + possible_action.move], a_idx] = 1
            feat[n2d["item/" + possible_action.item], a_idx] = 1
        return feat
