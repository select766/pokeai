"""
ポケモンの静的パラメータ（バトル中に変化しないもの）を表す
"""

import math
from typing import Tuple, List

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.poke_type import PokeType
import pokeai.sim.context as context


class PokeStatic:
    """
    ポケモンの静的パラメータ（バトル中に変化しないもの）を表す
    """

    """
    図鑑番号
    """
    dexno: Dexno
    """
    タイプ（1つか2つ）
    """
    poke_types: List[PokeType]
    """
    覚えている技
    """
    moves: List[Move]
    """
    ステータス
    """
    max_hp: int
    st_a: int
    st_b: int
    st_c: int
    st_s: int
    """
    素早さ種族値（急所判定に必要）
    """
    base_s: int
    lv: int

    @classmethod
    def create(cls, dexno: Dexno, moves: List[Move], lv: int = 50) -> "PokeStatic":
        """
        ポケモンを生成する。デフォルトでは理想個体。
        :param dexno:
        :return:
        """
        db = context.db
        base_stat = db.get_base_stat(dexno)
        pokest = PokeStatic()
        pokest.dexno = dexno
        pokest.moves = moves.copy()
        pokest.lv = lv
        pokest.poke_types = base_stat["types"]

        # 種族値などからステータス計算
        pokest.base_s = base_stat["s"]
        pokest.st_a = PokeStatic._calc_stat_abcs(lv, base_stat["a"])
        pokest.st_b = PokeStatic._calc_stat_abcs(lv, base_stat["b"])
        pokest.st_c = PokeStatic._calc_stat_abcs(lv, base_stat["c"])
        pokest.st_s = PokeStatic._calc_stat_abcs(lv, base_stat["s"])
        pokest.max_hp = PokeStatic._calc_stat_hp(lv, base_stat["h"])
        return pokest

    @staticmethod
    def _calc_stat_abcs(lv: int, bv: int, iv: int = 15, ev: int = 65535) -> int:
        """
        こうげき・ぼうぎょ・とくしゅ・すばやさのステータス計算。
        https://wiki.xn--rckteqa2e.com/wiki/%E3%82%B9%E3%83%86%E3%83%BC%E3%82%BF%E3%82%B9
        :param lv: レベル
        :param bv: 種族値
        :param iv: 個体値
        :param ev: 努力値
        :return:
        """
        return ((bv + iv) * 2 + int(math.ceil(math.sqrt(ev))) // 4) * lv // 100 + 5

    @staticmethod
    def _calc_stat_hp(lv: int, bv: int, iv: int = 15, ev: int = 65535) -> int:
        """
        HPのステータス計算。
        :param lv: レベル
        :param bv: 種族値
        :param iv: 個体値
        :param ev: 努力値
        :return:
        """
        return ((bv + iv) * 2 + int(math.ceil(math.sqrt(ev))) // 4) * lv // 100 + lv + 10
