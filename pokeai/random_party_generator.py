import os
import random

from pokeai.party_generator import PartyGenerator, Party, PartyPoke
from pokeai.dataset import DATASET_DIR
from pokeai.team_validator import TeamValidator
from pokeai.util import json_load


class RandomPartyGenerator(PartyGenerator):
    def __init__(self, regulation: str = "default"):
        self._validator = TeamValidator()
        self._pokedex = json_load(os.path.join(DATASET_DIR, 'pokedex.json'))
        self._regulation = json_load(os.path.join(DATASET_DIR, 'regulations', regulation, 'regulation.json'))
        self._learnsets = json_load(os.path.join(DATASET_DIR, 'regulations', regulation, 'learnsets.json'))

    def _single_random(self, level: int) -> PartyPoke:
        # 1体ランダム個体を生成(validationしない)
        species = random.choice(list(self._learnsets.keys()))
        # 性別固定ポケモンはgenderにその文字が、そうでなければ空文字列
        # 性別固定でなければ、攻撃個体値maxはオスとなる
        gender = self._pokedex[species]['gender'] or 'M'
        available_moves = self._learnsets[species]
        moves = random.sample(available_moves, min(4, len(available_moves)))
        return {
            'name': species,
            'species': species,
            'moves': moves,
            'ability': 'No Ability',
            'evs': {'hp': 255, 'atk': 255, 'def': 255, 'spa': 255, 'spd': 255, 'spe': 255},
            'ivs': {'hp': 30, 'atk': 30, 'def': 30, 'spa': 30, 'spd': 30, 'spe': 30},
            'item': '',
            'level': level,
            'shiny': False,
            'gender': gender,
            'nature': ''
        }

    def generate(self) -> Party:
        levels = self._regulation['levels'].copy()
        random.shuffle(levels)
        party: Party = []
        for level in levels:
            while True:
                cand = self._single_random(level)
                if self._validator.validate([cand]) is None:
                    break
            party.append(cand)
        val_error = self._validator.validate(party)
        if val_error:
            # 単体ではOKの個体の組み合わせでエラーになることは想定していない
            raise RuntimeError('party validation failed: ' + str(val_error))
        return party
