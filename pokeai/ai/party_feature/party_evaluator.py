# Q関数によるパーティ評価
from typing import List, Tuple

import numpy as np
import torch

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import PossibleAction
from pokeai.ai.dex import dex
from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.rl_policy_observation import RLPolicyObservation
from pokeai.sim.party_generator import Party

poke2id = dex._poke2id
id2poke = {v: k for k, v in poke2id.items()}


class PartyEvaluator:
    """
    パーティ及び対面ポケモンを与えてQ値を計算する
    """

    def __init__(self, agent: Agent, party_size: int):
        self.agent = agent
        self.party_size = party_size
        self.n_choices = 4 + self.party_size - 1

    def _make_request(self, party):
        return {'active': [
            {'moves': [{'move': move,  # 本来は先頭大文字だが使ってないので手抜き
                        'id': move, 'pp': 8, 'maxpp': 8, 'target': 'normal', 'disabled': False} for move in
                       party[0]["moves"]]}],
            'side': {'name': 'p1', 'id': 'p1', 'pokemon': [
                {'ident': 'p1: ' + id2poke[party[i]["species"]], 'details': id2poke[party[i]["species"]] + ', L55, M',
                 'condition': '215/215', 'active': i == 0,
                 'stats': {'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100}, 'moves': party[i]["moves"],
                 'baseAbility': 'noability', 'item': '', 'pokeball': 'pokeball'} for i in range(self.party_size)]}}

    def _make_obs(self, party: Party, opponent_poke: str) -> RLPolicyObservation:
        assert len(party) == self.party_size
        request = self._make_request(party)
        battle_status = BattleStatus("p1", party)
        for player in ["p1", "p2"]:
            battle_status.side_statuses[player].total_pokes = self.party_size
            battle_status.side_statuses[player].remaining_pokes = self.party_size
        # 最初に繰り出す
        battle_status.switch(f"p1a: {id2poke[party[0]['species']]}", f"{id2poke[party[0]['species']]}, L55, M",
                             "100/100")
        battle_status.switch(f"p2a: {id2poke[opponent_poke]}", f"{id2poke[opponent_poke]}, L55, M", "100/100")
        possible_actions: List[PossibleAction] = []
        active_poke = party[0]
        for i in range(len(active_poke["moves"])):
            possible_actions.append(PossibleAction(simulator_key=f"move {i + 1}",
                                                   poke=active_poke["species"],
                                                   move=active_poke["moves"][i],
                                                   switch=False,
                                                   force_switch=False,
                                                   allMoves=active_poke["moves"],
                                                   item=active_poke["item"]
                                                   ))
        for i in range(1, self.party_size):
            switch_poke = party[i]
            possible_actions.append(PossibleAction(simulator_key=f"switch {i + 1}",
                                                   poke=switch_poke["species"],
                                                   move=None,
                                                   switch=True,
                                                   force_switch=False,
                                                   allMoves=switch_poke["moves"],
                                                   item=switch_poke["item"]))
        obs = RLPolicyObservation(battle_status, request, possible_actions)
        return obs

    def _make_obs_vector(self, party: Party, opponent_poke: str) -> Tuple[np.ndarray, np.ndarray]:
        obs = self._make_obs(party, opponent_poke)
        obs_vector, action_mask = self.agent._feature_extractor.transform(obs)
        return obs_vector, action_mask

    def calc_q_func(self, party: Party, opponent_poke: str) -> np.ndarray:
        """
        パーティと対面ポケモンに対するq関数を計算する
        :param party: パーティ
        :param opponent_poke: ポケモンのid 例: "gyarados"
        :return: 各技に対応するq値
        """
        with torch.no_grad():
            obs_vector, action_mask = self._make_obs_vector(party, opponent_poke)
            q_vector = self.agent._calc_q_vector(obs_vector)
            q_vector[action_mask == 0] = -np.inf
        assert q_vector.shape == (self.n_choices,)
        return q_vector

    def gather_best_q(self, party: Party, opponent_pokes: List[str]) -> np.ndarray:
        obs_vectors = []
        action_masks = []
        for opponent_poke in opponent_pokes:
            obs, act = self._make_obs_vector(party, opponent_poke)
            obs_vectors.append(obs)
            action_masks.append(act)
        obs_vector_batch = np.stack(obs_vectors)
        action_mask_batch = np.stack(action_masks)
        with torch.no_grad():
            q_vectors = self.agent._calc_q_vector_batch(obs_vector_batch)
            q_vectors[action_mask_batch == 0] = -np.inf
        assert q_vectors.shape == (len(opponent_pokes), self.n_choices)
        return np.max(q_vectors, axis=1)
