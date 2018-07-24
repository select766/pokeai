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
    PSYCHC = 12
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
        return _type_match_dict[move_type].get(defend_type, 2)

    @classmethod
    def get_match_list(cls, move_type: "PokeType", defend_types: List["PokeType"]) -> List[int]:
        # 2倍→0.5倍と、0.5倍→2倍で結果が異なる場合あり。原作と一致しないかも。
        return [cls.get_match(move_type, t) for t in defend_types]


# https://wiki.ポケモン.com/wiki/%E7%9B%B8%E6%80%A7
# [技タイプ][受け側タイプ]
_type_match_dict = {}
_type_match_dict[PokeType.EMPTY] = {
}
_type_match_dict[PokeType.NORMAL] = {
    PokeType.ROCK: 1,
    PokeType.GHOST: 0,
}
_type_match_dict[PokeType.FIRE] = {
    PokeType.FIRE: 1,
    PokeType.WATER: 1,
    PokeType.GRASS: 4,
    PokeType.ICE: 4,
    PokeType.BUG: 4,
    PokeType.ROCK: 1,
    PokeType.DRAGON: 1,
}
_type_match_dict[PokeType.WATER] = {
    PokeType.FIRE: 1,
    PokeType.WATER: 1,
    PokeType.GRASS: 1,
    PokeType.GROUND: 4,
    PokeType.ROCK: 4,
    PokeType.DRAGON: 1,
}
_type_match_dict[PokeType.ELECTR] = {
    PokeType.WATER: 4,
    PokeType.ELECTR: 1,
    PokeType.GRASS: 1,
    PokeType.GROUND: 0,
    PokeType.FLYING: 4,
    PokeType.DRAGON: 1,
}
_type_match_dict[PokeType.GRASS] = {
    PokeType.FIRE: 1,
    PokeType.WATER: 4,
    PokeType.GRASS: 1,
    PokeType.POISON: 1,
    PokeType.GROUND: 4,
    PokeType.FLYING: 1,
    PokeType.BUG: 1,
    PokeType.ROCK: 4,
    PokeType.DRAGON: 1,
}
_type_match_dict[PokeType.ICE] = {
    PokeType.WATER: 1,
    PokeType.GRASS: 4,
    PokeType.ICE: 1,
    PokeType.GROUND: 4,
    PokeType.FLYING: 4,
    PokeType.DRAGON: 4,
}
_type_match_dict[PokeType.FIGHT] = {
    PokeType.NORMAL: 4,
    PokeType.ICE: 4,
    PokeType.POISON: 1,
    PokeType.FLYING: 1,
    PokeType.PSYCHC: 1,
    PokeType.BUG: 1,
    PokeType.ROCK: 4,
    PokeType.GHOST: 0,
}
_type_match_dict[PokeType.POISON] = {
    PokeType.GRASS: 4,
    PokeType.POISON: 1,
    PokeType.GROUND: 1,
    PokeType.BUG: 4,
    PokeType.ROCK: 1,
    PokeType.GHOST: 1,
}
_type_match_dict[PokeType.GROUND] = {
    PokeType.FIRE: 4,
    PokeType.ELECTR: 4,
    PokeType.GRASS: 1,
    PokeType.POISON: 4,
    PokeType.FLYING: 0,
    PokeType.BUG: 1,
    PokeType.ROCK: 4,
}
_type_match_dict[PokeType.FLYING] = {
    PokeType.ELECTR: 1,
    PokeType.GRASS: 4,
    PokeType.FIGHT: 4,
    PokeType.BUG: 4,
    PokeType.ROCK: 1,
}
_type_match_dict[PokeType.PSYCHC] = {
    PokeType.FIGHT: 4,
    PokeType.POISON: 4,
    PokeType.PSYCHC: 1,
}
_type_match_dict[PokeType.BUG] = {
    PokeType.FIRE: 1,
    PokeType.GRASS: 4,
    PokeType.FIGHT: 1,
    PokeType.POISON: 4,
    PokeType.FLYING: 1,
    PokeType.PSYCHC: 4,
    PokeType.GHOST: 1,
}
_type_match_dict[PokeType.ROCK] = {
    PokeType.FIRE: 4,
    PokeType.ICE: 4,
    PokeType.FIGHT: 1,
    PokeType.GROUND: 1,
    PokeType.FLYING: 4,
    PokeType.BUG: 4,
}
_type_match_dict[PokeType.GHOST] = {
    PokeType.NORMAL: 0,
    PokeType.PSYCHC: 0,
    PokeType.GHOST: 4,
}
_type_match_dict[PokeType.DRAGON] = {
    PokeType.DRAGON: 4,
}
