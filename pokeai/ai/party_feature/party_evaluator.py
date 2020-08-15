# Q関数によるパーティ評価
from typing import List

import numpy as np
import torch
from bson import ObjectId

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.dex import dex
from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.party_db import col_trainer, unpack_obj
from pokeai.ai.rl_policy_observation import RLPolicyObservation
from pokeai.sim.party_generator import Party

poke2id = dex._poke2id
id2poke = {v: k for k, v in poke2id.items()}


class PartyEvaluator:
    """
    パーティ及び対面ポケモンを与えてQ値を計算する
    """

    def __init__(self, agent: Agent):
        self.agent = agent

    def make_party(self, species: str, moves: List[str]) -> Party:
        """
        パーティを生成する。ポケモン1匹のみ。
        :param species: ポケモンID 例: "nidoqueen"
        :param moves: 技ID配列 例: ["thunderbolt", "fireblast", "bubblebeam", "firepunch"]
        :return:
        """
        return [{"name": species, "species": species, "moves": moves, "ability": "No Ability",
                 "evs": {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
                 "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30}, "item": "", "level": 55,
                 "shiny": False, "gender": "M", "nature": ""}]

    def _make_request(self, party):
        return {'active': [
            {'moves': [{'move': move,  # 本来は先頭大文字だが使ってないので手抜き
                        'id': move, 'pp': 8, 'maxpp': 8, 'target': 'normal', 'disabled': False} for move in
                       party[0]["moves"]]}],
            'side': {'name': 'p1', 'id': 'p1', 'pokemon': [
                {'ident': 'p1: ' + id2poke[party[0]["species"]], 'details': id2poke[party[0]["species"]] + ', L55, M',
                 'condition': '215/215', 'active': True,
                 'stats': {'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100}, 'moves': party[0]["moves"],
                 'baseAbility': 'noability', 'item': '', 'pokeball': 'pokeball'}]}}

    def _make_obs(self, party: Party, opponent_poke: str) -> RLPolicyObservation:
        request = self._make_request(party)
        battle_status = BattleStatus("p1", party)
        for player in ["p1", "p2"]:
            battle_status.side_statuses[player].total_pokes = 1
            battle_status.side_statuses[player].remaining_pokes = 1
        # 最初に繰り出す
        battle_status.switch(f"p1a: {id2poke[party[0]['species']]}", f"{id2poke[party[0]['species']]}, L55, M",
                             "100/100")
        battle_status.switch(f"p2a: {id2poke[opponent_poke]}", f"{id2poke[opponent_poke]}, L55, M", "100/100")
        obs = RLPolicyObservation(battle_status, request)
        return obs

    def _make_obs_vector(self, party: Party, opponent_poke: str) -> np.ndarray:
        obs = self._make_obs(party, opponent_poke)
        obs_vector, action_mask = self.agent._feature_extractor.transform(obs)
        return obs_vector[:, 0:4]  # 技4つ分だけ抽出（交代部分削除）

    def calc_q_func(self, party: Party, opponent_poke: str) -> np.ndarray:
        """
        パーティと対面ポケモンに対するq関数を計算する
        :param party: パーティ
        :param opponent_poke: ポケモンのid 例: "gyarados"
        :return: 各技に対応するq値
        """
        with torch.no_grad():
            q_vector = self.agent._calc_q_vector(self._make_obs_vector(party, opponent_poke))
        assert q_vector.shape == (4,)
        return q_vector

    def gather_best_q(self, party: Party, opponent_pokes: List[str]) -> np.ndarray:
        obs_vector_batch = np.stack([self._make_obs_vector(party, opponent_poke) for opponent_poke in opponent_pokes])
        with torch.no_grad():
            q_vectors = self.agent._calc_q_vector_batch(obs_vector_batch)
        assert q_vectors.shape == (len(opponent_pokes), 4)
        return np.max(q_vectors, axis=1)


def build_party_evaluator_by_trainer_id(trainer_id: ObjectId) -> PartyEvaluator:
    trainer_doc = col_trainer.find_one({"_id": trainer_id})
    trainer = Trainer.load_state(unpack_obj(trainer_doc["trainer_packed"]))
    agent = trainer.get_val_agent()
    return PartyEvaluator(agent)
