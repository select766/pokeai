# 通常の特徴抽出器を介さずに特徴合成することで、対面Q値計算を高速に行う
# Q関数によるパーティ評価

from typing import List, Tuple

import numpy as np
import torch

from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.party_feature.party_evaluator import PartyEvaluator
from pokeai.sim.party_generator import Party
from pokeai.util import json_load, DATASET_DIR

sample_party = [
    {"name": "octillery", "species": "octillery", "moves": ["toxic", "bubblebeam", "flamethrower"],
     "ability": "No Ability", "evs": {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
     "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30}, "item": "", "level": 55,
     "shiny": False, "gender": "M", "nature": ""},
    {"name": "snorlax", "species": "snorlax", "moves": ["icebeam", "bubblebeam", "dynamicpunch", "takedown"],
     "ability": "No Ability", "evs": {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
     "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30}, "item": "", "level": 50,
     "shiny": False, "gender": "M", "nature": ""},
    {"name": "omastar", "species": "omastar", "moves": ["bodyslam", "skullbash", "hiddenpowergrass", "icebeam"],
     "ability": "No Ability", "evs": {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
     "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30}, "item": "", "level": 50,
     "shiny": False, "gender": "M", "nature": ""}
]


class PartyEvaluatorQuick(PartyEvaluator):
    def __init__(self, agent: Agent, party_size: int, device: str):
        super().__init__(agent, party_size)
        self.device = device
        self.model = self.agent._model.to(self.device)
        self.all_pokemons = json_load(DATASET_DIR.joinpath("all_pokemons.json"))
        self.pokemon_to_idx = {name: i for i, name in enumerate(self.all_pokemons)}
        self.all_moves = json_load(DATASET_DIR.joinpath("all_moves_with_hiddenpower_type.json"))
        self.move_to_idx = {name: i + len(self.all_pokemons) for i, name in enumerate(self.all_moves)}

        self._state_vecs = {opponent_poke: self._make_state(opponent_poke) for opponent_poke in self.all_pokemons}
        self._state_vec_length = self._state_vecs[self.all_pokemons[0]].shape[0]

        self._validate()

    def _make_state(self, opponent_poke: str) -> np.ndarray:
        obs = self._make_obs(sample_party[:self.party_size], opponent_poke)
        # 状態ベクトルに自分側パーティの具体的なポケモン・技は関与しないので、何らかの有効なパーティで生成したものを使いまわす
        return self.agent._feature_extractor.state_feature_extractor.transform(obs)

    def _make_obs_vector_batch(self, party: Party, opponent_pokes: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        obs = self._make_obs(party, "suicune")  # 相手情報はchoice_to_vecには関係ない
        # shape=(選択肢ベクトルの長さ, self.n_choices)
        choice_vec = self.agent._feature_extractor.choice_to_vec.transform(obs)
        obs_vector_batch = np.zeros((len(opponent_pokes), self._state_vec_length + choice_vec.shape[0], self.n_choices),
                                    dtype=np.float32)
        action_mask_batch = np.zeros((len(opponent_pokes), self.n_choices), dtype=np.float32)
        for i, opponent_poke in enumerate(opponent_pokes):
            obs_vector_batch[i, :self._state_vec_length, :] = self._state_vecs[opponent_poke][:, np.newaxis]
        obs_vector_batch[:, self._state_vec_length:, :choice_vec.shape[1]] = choice_vec
        action_mask_batch[:, :len(obs.possible_actions)] = 1
        return obs_vector_batch, action_mask_batch

    def _validate(self):
        """
        オリジナルのPartyEvaluatorと同一の特徴生成ができることを確認する
        :return:
        """
        opponent_pokes = ["miltank", "gyarados"]
        super_obj = PartyEvaluator(self.agent, self.party_size)
        obs_vectors = []
        action_masks = []
        for opponent_poke in opponent_pokes:
            obs, act = super_obj._make_obs_vector(sample_party[:self.party_size], opponent_poke)
            obs_vectors.append(obs)
            action_masks.append(act)
        obs_vector_batch = np.stack(obs_vectors)
        action_mask_batch = np.stack(action_masks)

        this_obs_vector_batch, this_action_mask_batch = self._make_obs_vector_batch(sample_party[:self.party_size],
                                                                                    opponent_pokes)
        assert np.allclose(obs_vector_batch, this_obs_vector_batch)
        assert np.allclose(action_mask_batch, this_action_mask_batch)

    def calc_q_func(self, party: Party, opponent_poke: str) -> np.ndarray:
        """
        パーティと対面ポケモンに対するq関数を計算する
        :param party: パーティ
        :param opponent_poke: ポケモンのid 例: "gyarados"
        :return: 各技に対応するq値
        """
        obs_vector_batch, action_mask_batch = self._make_obs_vector_batch(party, [opponent_poke])
        with torch.no_grad():
            q_vector = self.model(torch.from_numpy(obs_vector_batch).to(self.device)).to("cpu").numpy()[0]
            q_vector[action_mask_batch[0] == 0] = -np.inf
        assert q_vector.shape == (self.n_choices,)
        return q_vector

    def gather_best_q(self, party: Party, opponent_pokes: List[str]) -> np.ndarray:
        obs_vector_batch, action_mask_batch = self._make_obs_vector_batch(party, opponent_pokes)
        with torch.no_grad():
            q_vectors = self.model(torch.from_numpy(obs_vector_batch).to(self.device)).to("cpu").numpy()
            q_vectors[action_mask_batch == 0] = -np.inf
        assert q_vectors.shape == (len(opponent_pokes), self.n_choices)
        return np.max(q_vectors, axis=1)
