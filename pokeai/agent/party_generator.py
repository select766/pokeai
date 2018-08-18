"""
ゲームシステム上有効なパーティのランダム生成・置換機構。
"""
import copy
import random
from enum import Enum, auto
from typing import List, Dict, Tuple
import os
import json
from collections import defaultdict
import numpy as np

from pokeai.agent.util import randint_len
from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.move_learn_condition import MoveLearnType
from pokeai.sim.move_learn_db import move_learn_db
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.move_info_db import move_info_db


class PossiblePokeDB:
    """
    あるレベルでのポケモン・技のありうる構成を示すデータベース
    """

    allow_rare: bool
    data: Dict[Dexno, List[Tuple[Move, int]]]  # ポケモンごとに、覚える技とそのレベル
    min_level: Dict[Dexno, int]  # 入手可能最低レベル

    def __init__(self, allow_rare: bool):
        self.allow_rare = allow_rare
        self._construct_db()

    def _construct_db(self):
        with open(os.path.join(os.path.dirname(__file__), "party_generation_db.json")) as f:
            db = json.load(f)
        dexno_move_lv = {}  # [dexno][move] = 覚える最低lv
        self.min_level = {}
        # LVアップ、技マシン技を追加
        for dexno, mlcs in move_learn_db.items():
            # 技マシン技はLV0扱い
            dexno_move_lv[dexno] = {mlc.move: mlc.lv for mlc in mlcs}
        # 野生で入手する場合の最低レベル設定
        for dexno_int, lv in db["wild_min_levels"]:
            # 野生入手できないとき0が入っている
            self.min_level[Dexno(dexno_int)] = lv
        # 進化により、進化前の技を継承
        # LV16で進化→進化前がLV16以下で覚える技をLV16で覚え、LV20で覚える技はLV20で覚えるとして設定
        # レベルアップで2段階進化する場合、注意が必要
        # ゼニガメがハイドロポンプをLV42で覚えるが、レベル進化は1上がるごとに1段階しかできないため
        # カメールが継承できるのはLV42に対し、カメックスが継承できるのはLV43
        # LV進化のあと石進化ならこれは起きない
        # LV2段進化だけ特殊扱いする。初代ではこれで十分。金銀でも1段階目LV以外→2段階目LVというのはない。
        # LV2段進化のとき、1つ前からはLVそのまま、2つ前からはLV+1して技を継承。
        # 進化して技マシンが使えなくなるということはないはずなので、技マシン技には影響なし。
        # 継承技とLVUP技が混ざらないよう、最終進化系から先に調べる
        # 初代では、図鑑番号が大きいほうが最終進化系と考えてよい
        evol_to_from = {e_to: (e_from, e_lv) for e_to, e_from, e_lv in db["evolution_levels"]}
        for dexno_int in reversed(sorted(evol_to_from.keys())):  # 図鑑番号が大きいほうから
            dexno = Dexno(dexno_int)
            move_lv = dexno_move_lv[dexno]
            evol_from_1, evol_from_1_lv = evol_to_from[dexno_int]  # 1段階前
            evol_from_1_dexno = Dexno(evol_from_1)
            if evol_from_1 in evol_to_from:
                # 2段階前
                evol_from_2, evol_from_2_lv = evol_to_from[evol_from_1]
                evol_from_2_dexno = Dexno(evol_from_2)
                lvlv = evol_from_1_lv != 0 and evol_from_2_lv != 0  # 2段階ともレベル進化
                if self.min_level[dexno] == 0:
                    # レベル進化ならそのレベル、石進化(lv0)なら進化前の最低入手レベル
                    if self.min_level[evol_from_1_dexno] > 0:
                        # 1段階前が直接手に入る
                        self.min_level[dexno] = max(evol_from_1_lv, self.min_level[evol_from_1_dexno])
                    else:
                        # 2段階前から進化させる必要あり
                        self.min_level[dexno] = max(evol_from_1_lv, evol_from_2_lv, self.min_level[evol_from_2_dexno])
                # 技継承
                for inherit_move, inherit_move_lv in dexno_move_lv[evol_from_1_dexno].items():
                    inherit_move_lv = max(inherit_move_lv, evol_from_1_lv)  # 進化レベルより前で覚えても進化レベルになるまで継承できない
                    if inherit_move not in move_lv or move_lv[inherit_move] > inherit_move_lv:
                        move_lv[inherit_move] = inherit_move_lv
                # 2段階前から技継承
                for inherit_move, inherit_move_lv in dexno_move_lv[evol_from_2_dexno].items():
                    if lvlv:
                        inherit_move_lv += 1
                    inherit_move_lv = max(inherit_move_lv, evol_from_1_lv,
                                          evol_from_2_lv)  # 進化レベルより前で覚えても進化レベルになるまで継承できない
                    if inherit_move not in move_lv or move_lv[inherit_move] > inherit_move_lv:
                        move_lv[inherit_move] = inherit_move_lv
            else:
                # 1段階のみ進化
                if self.min_level[dexno] == 0:
                    # レベル進化ならそのレベル、石進化(lv0)なら進化前の最低入手レベル
                    self.min_level[dexno] = max(evol_from_1_lv, self.min_level[evol_from_1_dexno])
                # 技継承
                for inherit_move, inherit_move_lv in dexno_move_lv[evol_from_1_dexno].items():
                    inherit_move_lv = max(inherit_move_lv, evol_from_1_lv)  # 進化レベルより前で覚えても進化レベルになるまで継承できない
                    if inherit_move not in move_lv or move_lv[inherit_move] > inherit_move_lv:
                        move_lv[inherit_move] = inherit_move_lv
        self.data = {dexno: [(move, lv) for move, lv in move_lv.items()] for dexno, move_lv in dexno_move_lv.items()}
        if not self.allow_rare:
            # 入手レベルを101にすることで伝説利用不可とする
            for dexno_int in db["rares"]:
                self.min_level[Dexno(dexno_int)] = 101
        self._drop_not_impelemted_moves()

    def _drop_not_impelemted_moves(self):
        implemented_moves = set(move_info_db.keys())
        for dexno in list(self.data.keys()):
            movelist = self.data[dexno]
            new_movelist = [item for item in movelist if item[0] in implemented_moves]
            self.data[dexno] = new_movelist

    def get_leanable_moves(self, dexno: Dexno, lv: int) -> List[Move]:
        """
        指定したポケモンが特定レベル時点で覚えられる技のリストを取得する。
        特定レベルでは入手できないポケモンについては空のリストが返る。
        :param dexno:
        :param lv:
        :return:
        """
        if self.min_level[dexno] > lv:
            return []
        return [move for move, lv_ in self.data[dexno] if lv >= lv_]


class PartyRule(Enum):
    LV55_1 = auto()
    LV100_1 = auto()
    LV30_3 = auto()
    LV50_3 = auto()
    LVSUM155_3 = auto()


class PartyGenerator:
    db: PossiblePokeDB
    n_member: int
    lvs: List[int]

    def __init__(self, rule: PartyRule, allow_rare: bool = False):
        self.db = PossiblePokeDB(allow_rare=allow_rare)
        if rule is PartyRule.LV55_1:
            self.lvs = [55]
        elif rule is PartyRule.LV100_1:
            self.lvs = [100]
        elif rule is PartyRule.LV30_3:
            self.lvs = [30, 30, 30]
        elif rule is PartyRule.LV50_3:
            self.lvs = [50, 50, 50]
        elif rule is PartyRule.LVSUM155_3:
            # 本来配分は自由([53,52,50]等もあり)だが当面固定
            self.lvs = [55, 50, 50]
        self.n_member = len(self.lvs)

    def generate(self) -> Party:
        pokests = []
        dexnos = set()
        for lv in self.lvs:
            while True:
                dexno = random.choice(list(Dexno))
                if dexno in dexnos:
                    continue
                learnable_moves = self.db.get_leanable_moves(dexno, lv)
                if len(learnable_moves) == 0:
                    continue
                moves = random.sample(learnable_moves, min(4, len(learnable_moves)))
                pokest = PokeStatic.create(dexno, moves, lv)
                pokests.append(pokest)
                dexnos.add(dexno)
                break
        random.shuffle(pokests)  # 先頭をLV55に固定しない
        return Party(pokests)

    def generate_neighbor_party(self, party: Party) -> Party:
        """
        近傍の(技を1個だけ変更した)パーティを生成する。
        :param party:
        :return:
        """
        assert len(party.pokes) == 1
        pokest = copy.deepcopy(party.pokes[0].poke_static)
        moves = pokest.moves
        learnable_moves = self.db.get_leanable_moves(pokest.dexno, pokest.lv)
        for m in moves:
            learnable_moves.remove(m)
        if len(learnable_moves) == 0 and len(moves) == 1:
            # 技を1つしか覚えないポケモン(LV15未満のコイキング等)
            # どうしようもない
            pass
        elif len(learnable_moves) == 0 or (np.random.random() < 0.1 and len(moves) > 1):
            # 技を消す
            moves.pop(randint_len(moves))
        elif np.random.random() < 0.1 and len(moves) < 4:
            # 技を足す
            moves.append(learnable_moves[randint_len(learnable_moves)])
        else:
            # 技を変更する
            new_move = learnable_moves[randint_len(learnable_moves)]
            moves[randint_len(moves)] = new_move
        return Party([pokest])
