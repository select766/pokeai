"""
ゲームシステム上有効なパーティのランダム生成・置換機構。
"""
from typing import List, Dict, Tuple
import os
import json
from collections import defaultdict

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.move_learn_condition import MoveLearnType
from pokeai.sim.move_learn_db import move_learn_db


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


class PartyGenerator:
    def __init__(self, n_member: int, lv_min: int, lv_max: int, lv_sum: int, allow_rare: bool):
        pass

    def generate(self):
        pass
