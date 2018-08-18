"""
ポケモン・技評価値をもとにランダムなパーティ群を生成する。
評価値が高い要素が選ばれやすくなる。
"""
import random
import os
import json
from collections import defaultdict
from typing import Dict, Union, List
import numpy as np

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic


class PartyGeneratorWithMoveValue(PartyGenerator):
    def __init__(self, scores: Dict[Union[Dexno, Move], float], temperature: float, rule: PartyRule,
                 allow_rare: bool = False):
        super().__init__(rule, allow_rare)
        self.scores = scores
        self.temperature = temperature

        # dexnoについては確率分布を事前計算
        assert all(lv == self.lvs[0] for lv in self.lvs), "複数LVのパーティは未対応"
        lv = self.lvs[0]
        dexnos = []
        dexno_scores = []
        dexno_moves = {}
        dexno_move_weights = {}
        for dexno in Dexno:
            learnable_moves = self.db.get_leanable_moves(dexno, lv)
            if len(learnable_moves) == 0:
                # 使用不可ポケモン
                continue
            dexno_moves[dexno] = learnable_moves
            move_scores = [scores[move] for move in learnable_moves]
            dexno_move_weights[dexno] = self._softmax(move_scores)
            dexnos.append(dexno)
            dexno_scores.append(scores[dexno])
        dexno_weights = self._softmax(dexno_scores)
        self.dexnos = dexnos
        self.dexno_weights = dexno_weights
        self.dexno_moves = dexno_moves
        self.dexno_move_weights = dexno_move_weights

    def _softmax(self, values):
        """
        スコアをsoftmax確率としてrandom.choicesで使えるweightsに変換
        :param values:
        :return:
        """
        vec = np.array(values, dtype=np.float)
        vec -= np.max(vec)
        vec /= self.temperature
        vec_exp = np.exp(vec)
        probs = vec_exp / np.sum(vec_exp)
        return list(probs)

    def generate(self) -> Party:
        pokests = []
        dexnos = set()
        for lv in self.lvs:
            while True:
                dexno = random.choices(self.dexnos, weights=self.dexno_weights)[0]
                if dexno in dexnos:
                    continue
                ms = self.dexno_moves[dexno]
                if len(ms) <= 4:
                    moves = ms[:]
                else:
                    moves = []
                    mws = self.dexno_move_weights[dexno]
                    while len(moves) < 4:
                        move = random.choices(ms, weights=mws)[0]
                        if move not in moves:
                            moves.append(move)
                pokest = PokeStatic.create(dexno, moves, lv)
                pokests.append(pokest)
                dexnos.add(dexno)
                break
        random.shuffle(pokests)  # 先頭をLV55に固定しない
        return Party(pokests)
