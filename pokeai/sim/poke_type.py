"""
ポケモンのタイプ定数
"""

from enum import Enum
from typing import List


class PokeType(Enum):
    """
    ポケモンのタイプ定数
    """
    EMPTY = 1
    NORMAL = 2
    FIRE = 3
    WATER = 4
    ELECTR = 5
    GRASS = 6
    ICE = 7
    FIGHT = 8
    POISON = 9
    GROUND = 10
    FLYING = 11
    PHYCHC = 12
    BUG = 13
    ROCK = 14
    GHOST = 15
    DRAGON = 16

    @classmethod
    def is_physical(cls, move_type: "PokeType"):
        # 物理技となるタイプ
        physical_types = [PokeType.NORMAL, PokeType.FIGHT, PokeType.POISON, PokeType.GROUND,
                          PokeType.FLYING, PokeType.BUG, PokeType.ROCK, PokeType.GHOST]
        return move_type in physical_types

    @classmethod
    def get_match(cls, move_type: "PokeType", defend_type: "PokeType") -> int:
        """
        タイプ相性を計算する。2倍した整数を返す。等倍なら2、半減なら1、無効なら0。
        :param move_type:
        :param defend_type:
        :return:
        """
        # TODO: テーブル用意
        if move_type == PokeType.FIRE and defend_type == PokeType.GRASS:
            return 4
        return 2

    @classmethod
    def get_match_list(cls, move_type: "PokeType", defend_types: List["PokeType"]) -> List[int]:
        return [cls.get_match(move_type, t) for t in defend_types]
