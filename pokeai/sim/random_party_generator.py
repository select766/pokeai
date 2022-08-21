import copy
import random
from typing import Set, Optional, List
from pokeai.sim.model import Party, PartyPoke

from pokeai.sim.party_generator import PartyGenerator
from pokeai.util import DATASET_DIR
from pokeai.sim.team_validator import TeamValidator
from pokeai.util import json_load


class RandomPartyGenerator(PartyGenerator):
    def __init__(self,
                 regulation: str = "default",
                 neighbor_poke_change_rate: float = 0.1,
                 neighbor_item_change_rate: float = 0.1):
        self._validator = TeamValidator()
        self._pokedex = json_load(DATASET_DIR.joinpath('pokedex.json'))
        self._lv55_pokemons = json_load(DATASET_DIR.joinpath('lv55_pokemons.json'))
        self._regulation = json_load(DATASET_DIR.joinpath('regulations', regulation, 'regulation.json'))
        self._learnsets = json_load(DATASET_DIR.joinpath('regulations', regulation, 'learnsets.json'))
        self._pokemons = json_load(DATASET_DIR.joinpath('regulations', regulation, 'pokemons.json'))
        self._items = json_load(DATASET_DIR.joinpath('regulations', regulation, 'items.json'))
        self.neighbor_poke_change_rate = neighbor_poke_change_rate
        self.neighbor_item_change_rate = neighbor_item_change_rate if len(self._items) > 0 else 0.0

    @property
    def party_size(self) -> int:
        return len(self._regulation['levels'])

    def _single_random(self, level: int, species: Optional[str] = None) -> PartyPoke:
        # 1体ランダム個体を生成(validationしない)
        if species is None:
            species = random.choice(list(self._pokemons))
        # 性別固定ポケモンはgenderにその文字が、そうでなければ空文字列
        # 性別固定でなければ、攻撃個体値maxはオスとなる
        gender = self._pokedex[species]['gender'] or 'M'
        available_moves = self._learnsets[species]
        moves = random.sample(available_moves, min(4, len(available_moves)))
        item = random.choice(self._items) if len(self._items) > 0 else ''  # アイテムなしを選ぶにはitems.jsonに''のエントリを挿入
        return {
            'name': species,
            'species': species,
            'moves': moves,
            'ability': 'No Ability',
            'evs': {'hp': 255, 'atk': 255, 'def': 255, 'spa': 255, 'spd': 255, 'spe': 255},
            'ivs': {'hp': 30, 'atk': 30, 'def': 30, 'spa': 30, 'spd': 30, 'spe': 30},
            'item': item,
            'level': level,
            'shiny': False,
            'gender': gender,
            'nature': ''
        }

    def _shuffle_levels_for_species(self, species: List[str]):
        """
        種族のレベル制限に合うようにレベルをシャッフルする
        :param species:
        :return:
        """
        if self._regulation['levels'] == [55, 50, 50]:
            # LV55, 50, 50で、LV55でしか存在できないポケモンがいるという状況に決め打ちの実装
            # LV55専用ポケモンがいる場合、その箇所を55、残りを50
            lv55_idxs = []
            for i, sp in enumerate(species):
                if sp in self._lv55_pokemons:
                    lv55_idxs.append(i)
            if len(lv55_idxs) > 1:
                raise ValueError('More than one lv55-only pokemons')
            elif len(lv55_idxs) == 1:
                levels = [50, 50, 50]
                levels[lv55_idxs[0]] = 55
            else:
                levels = self._regulation['levels'].copy()
                random.shuffle(levels)
            return levels
        elif self._regulation['levels'] == [55]:
            return [55]
        else:
            raise NotImplementedError('_shuffle_levels_for_species is not implemented for this levels')

    def generate(self, fix_species: Optional[List[str]] = None) -> Party:
        """
        ランダムなパーティを1つ生成する。
        :param fix_species: 使用するポケモンの種族を固定する場合、パーティのポケモン数分の種族名リスト。シャッフルせずに使用される。ex. ["gyarados", "dugtrio", "ninetales"]
        :return:
        """
        if fix_species is not None:
            levels = self._shuffle_levels_for_species(fix_species)
        else:
            levels = self._regulation['levels'].copy()
            random.shuffle(levels)
        party: Party = []
        species: Set[str] = set()
        items: Set[str] = set()
        abort_ctr = 0
        for level in levels:
            while True:
                cand = self._single_random(level, fix_species[len(party)] if fix_species is not None else None)
                # ポケモン単体でおかしくないか＆種族が被っていないか
                # アイテムなしは重複可能
                if (cand['species'] not in species) and ((cand['item'] == '') or (cand['item'] not in items)) and (
                        self._validator.validate([cand]) is None):
                    break
                abort_ctr += 1
                if abort_ctr > 100:
                    raise ValueError('Failed to find a party which satisfies constraints')
            party.append(cand)
            species.add(cand['species'])
            items.add(cand['item'])
        val_error = self._validator.validate(party)
        if val_error:
            # 単体ではOKの個体の組み合わせでエラーになることは想定していない
            raise RuntimeError('party validation failed: ' + str(val_error))
        return party

    def neighbor(self, party: Party) -> Party:
        """
        近傍パーティを生成する
        :param party:
        :return:ポケモン1匹か、ポケモン1匹の技1つか、道具を変更したパーティ。まれに変更なしの場合あり。
        """
        new_party = copy.deepcopy(party)
        change_idx = random.randrange(len(new_party))  # 変更するポケモンのindex
        rnd = random.random()
        if self.neighbor_poke_change_rate > rnd:
            # ポケモンを変更
            species = {poke['species'] for i, poke in enumerate(new_party) if i != change_idx}
            while True:
                cand = self._single_random(new_party[change_idx]['level'])
                # ポケモン単体でおかしくないか＆種族が被っていないか
                if (cand['species'] not in species) and (self._validator.validate([cand]) is None):
                    break
            new_party[change_idx] = cand
        else:
            rnd -= self.neighbor_poke_change_rate
            change_poke = new_party[change_idx]
            if self.neighbor_item_change_rate > rnd:
                # アイテムの変更
                items = {poke['item'] for i, poke in enumerate(new_party) if i != change_idx}  # 他のポケモンが持っているアイテム
                cur_item = change_poke['item']
                while True:
                    new_item = random.choice(self._items)
                    if new_item != cur_item and new_item not in items:
                        change_poke['item'] = new_item
                        break
            else:
                # 技を変更
                available_moves = self._learnsets[change_poke['species']]
                current_moves = change_poke['moves'].copy()
                if len(available_moves) > 4:  # 覚えられる技が4つ以下なら選択の余地なし
                    for i in range(100):  # 技は4つより多いものの、両立不可によりどうしても変更できない場合の無限ループ回避
                        change_move_idx = random.randrange(len(current_moves))
                        new_move = random.choice(available_moves)
                        if new_move in current_moves:
                            continue
                        change_poke['moves'][change_move_idx] = new_move
                        # 両立不可などの理由でダメな場合を弾く
                        if self._validator.validate([change_poke]) is None:
                            break
                        # 変えた技を元に戻す
                        change_poke['moves'][change_move_idx] = current_moves[change_move_idx]
        val_error = self._validator.validate(new_party)
        if val_error:
            # 単体ではOKの個体の組み合わせでエラーになることは想定していない
            raise RuntimeError('party validation failed: ' + str(val_error))
        return new_party
