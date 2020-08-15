# 通常の特徴抽出器を介さずに特徴合成することで、対面Q値計算を高速に行う
# Q関数によるパーティ評価

from typing import List

import numpy as np
import torch
from bson import ObjectId

from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.party_db import col_trainer, unpack_obj
from pokeai.ai.party_feature.party_evaluator import PartyEvaluator
from pokeai.sim.party_generator import Party
from pokeai.util import json_load, DATASET_DIR


class PartyEvaluatorQuick(PartyEvaluator):
    def __init__(self, agent: Agent, device: str):
        super().__init__(agent)
        self.device = device
        self.model = self.agent._model.to(self.device)
        self.all_pokemons = json_load(DATASET_DIR.joinpath("all_pokemons.json"))
        self.pokemon_to_idx = {name: i for i, name in enumerate(self.all_pokemons)}
        self.all_moves = json_load(DATASET_DIR.joinpath("all_moves.json"))
        self.move_to_idx = {name: i + len(self.all_pokemons) for i, name in enumerate(self.all_moves)}

        self._state_vecs = {opponent_poke: self._make_state(opponent_poke) for opponent_poke in self.all_pokemons}
        self._state_vec_length = self._state_vecs[self.all_pokemons[0]].shape[0]

        self._validate()

    def _make_state(self, opponent_poke: str) -> np.ndarray:
        sample_party = [
            {"name": "suicune", "species": "suicune", "moves": ["surf", "hyperbeam", "icebeam", "waterfall"],
             "ability": "No Ability", "evs": {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
             "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30}, "item": "", "level": 55,
             "shiny": False, "gender": "N", "nature": ""}]
        choice_vec = np.array([1, 1, 1, 1, 0, 0], dtype=np.float32)  # 技4つ使用可能、交代不可能
        obs = self._make_obs(sample_party, opponent_poke)
        # 自分側パーティは関与しないはず
        return self.agent._feature_extractor.state_feature_extractor.transform(obs.battle_status, choice_vec)

    def _make_obs_vector_batch(self, party: Party, opponent_pokes: List[str]) -> np.ndarray:
        obs = self._make_obs(party, "suicune")  # 相手情報はchoice_to_vecには関係ない
        # shape=(選択肢ベクトルの長さ, 4(技の数))
        choice_vec = self.agent._feature_extractor.choice_to_vec.transform(obs.battle_status, obs.request)
        obs_vector_batch = np.zeros((len(opponent_pokes), self._state_vec_length + choice_vec.shape[0], 4),
                                    dtype=np.float32)
        for i, opponent_poke in enumerate(opponent_pokes):
            obs_vector_batch[i, :self._state_vec_length, :] = self._state_vecs[opponent_poke][:, np.newaxis]
        obs_vector_batch[:, self._state_vec_length:, :] = choice_vec
        return obs_vector_batch

    def _validate(self):
        """
        オリジナルのPartyEvaluatorと同一の特徴生成ができることを確認する
        :return:
        """
        sample_party = [{"name": "kangaskhan", "species": "kangaskhan",
                         "moves": ["thunder", "flamethrower", "fireblast", "seismictoss"], "ability": "No Ability",
                         "evs": {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
                         "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30}, "item": "",
                         "level": 55, "shiny": False, "gender": "F", "nature": ""}]
        opponent_pokes = ["miltank", "gyarados"]
        super_obj = PartyEvaluator(self.agent)
        super_obs_vector_batch = np.stack(
            [super_obj._make_obs_vector(sample_party, opponent_poke) for opponent_poke in opponent_pokes])
        this_obs_vector_batch = self._make_obs_vector_batch(sample_party, opponent_pokes)
        assert np.allclose(super_obs_vector_batch, this_obs_vector_batch)

    def calc_q_func(self, party: Party, opponent_poke: str) -> np.ndarray:
        """
        パーティと対面ポケモンに対するq関数を計算する
        :param party: パーティ
        :param opponent_poke: ポケモンのid 例: "gyarados"
        :return: 各技に対応するq値
        """
        obs_vector_batch = self._make_obs_vector_batch(party, [opponent_poke])
        with torch.no_grad():
            q_vector = self.model(torch.from_numpy(obs_vector_batch).to(self.device)).to("cpu").numpy()[0]
        assert q_vector.shape == (4,)
        return q_vector

    def gather_best_q(self, party: Party, opponent_pokes: List[str]) -> np.ndarray:
        obs_vector_batch = self._make_obs_vector_batch(party, opponent_pokes)
        with torch.no_grad():
            q_vectors = self.model(torch.from_numpy(obs_vector_batch).to(self.device)).to("cpu").numpy()
        assert q_vectors.shape == (len(opponent_pokes), 4)
        return np.max(q_vectors, axis=1)


def build_party_evaluator_quick_by_trainer_id(trainer_id: ObjectId, device="cuda:0") -> PartyEvaluatorQuick:
    trainer_doc = col_trainer.find_one({"_id": trainer_id})
    trainer = Trainer.load_state(unpack_obj(trainer_doc["trainer_packed"]))
    agent = trainer.get_val_agent()
    return PartyEvaluatorQuick(agent, device)
