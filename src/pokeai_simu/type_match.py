# -*- coding:utf-8 -*-

"""
タイプ相性計算
"""

from .poke_type import PokeType
from .poke import Poke

# https://wiki.ポケモン.com/wiki/%E7%9B%B8%E6%80%A7
# [技タイプ][受け側タイプ]
_type_match_dict = {}
_type_match_dict[PokeType.Empty] = {
}
_type_match_dict[PokeType.Normal] = {
    PokeType.Rock: 1,
    PokeType.Ghost: 0,
}
_type_match_dict[PokeType.Fire] = {
    PokeType.Fire: 1,
    PokeType.Water: 1,
    PokeType.Grass: 4,
    PokeType.Ice: 4,
    PokeType.Bug: 4,
    PokeType.Rock: 1,
    PokeType.Dragon: 1,
}
_type_match_dict[PokeType.Water] = {
    PokeType.Fire: 1,
    PokeType.Water: 1,
    PokeType.Grass: 4,
    PokeType.Ground: 4,
    PokeType.Rock: 4,
    PokeType.Dragon: 1,
}
_type_match_dict[PokeType.Electr] = {
    PokeType.Water: 4,
    PokeType.Electr: 1,
    PokeType.Grass: 1,
    PokeType.Ground: 0,
    PokeType.Flying: 4,
    PokeType.Dragon: 1,
}
_type_match_dict[PokeType.Grass] = {
    PokeType.Fire: 1,
    PokeType.Water: 4,
    PokeType.Grass: 1,
    PokeType.Poison: 1,
    PokeType.Ground: 4,
    PokeType.Flying: 1,
    PokeType.Bug: 1,
    PokeType.Rock: 4,
    PokeType.Dragon: 1,
}
_type_match_dict[PokeType.Ice] = {
    PokeType.Water: 1,
    PokeType.Grass: 4,
    PokeType.Ice: 1,
    PokeType.Ground: 4,
    PokeType.Flying: 4,
    PokeType.Dragon: 4,
}
_type_match_dict[PokeType.Fight] = {
    PokeType.Normal: 4,
    PokeType.Ice: 4,
    PokeType.Poison: 1,
    PokeType.Flying: 1,
    PokeType.Psychc: 1,
    PokeType.Bug: 1,
    PokeType.Rock: 4,
    PokeType.Ghost: 0,
}
_type_match_dict[PokeType.Poison] = {
    PokeType.Grass: 4,
    PokeType.Poison: 1,
    PokeType.Ground: 1,
    PokeType.Bug: 4,
    PokeType.Rock: 1,
    PokeType.Ghost: 1,
}
_type_match_dict[PokeType.Ground] = {
    PokeType.Fire: 4,
    PokeType.Electr: 4,
    PokeType.Grass: 1,
    PokeType.Poison: 4,
    PokeType.Flying: 0,
    PokeType.Bug: 1,
    PokeType.Rock: 4,
}
_type_match_dict[PokeType.Flying] = {
    PokeType.Electr: 1,
    PokeType.Grass: 4,
    PokeType.Fight: 4,
    PokeType.Bug: 4,
    PokeType.Rock: 1,
}
_type_match_dict[PokeType.Psychc] = {
    PokeType.Fight: 4,
    PokeType.Poison: 4,
    PokeType.Psychc: 1,
}
_type_match_dict[PokeType.Bug] = {
    PokeType.Fire: 1,
    PokeType.Grass: 4,
    PokeType.Fight: 1,
    PokeType.Poison: 4,
    PokeType.Flying: 1,
    PokeType.Psychc: 4,
    PokeType.Ghost: 1,
}
_type_match_dict[PokeType.Rock] = {
    PokeType.Fire: 4,
    PokeType.Ice: 4,
    PokeType.Fight: 1,
    PokeType.Ground: 1,
    PokeType.Flying: 4,
    PokeType.Bug: 4,
}
_type_match_dict[PokeType.Ghost] = {
    PokeType.Normal: 0,
    PokeType.Psychc: 0,
    PokeType.Ghost: 4,
}
_type_match_dict[PokeType.Dragon] = {
    PokeType.Dragon: 4,
}


def get_type_match_x2(move_poke_type, enemy_poke_type):
    """
    単一のタイプ相性計算
    """
    return _type_match_dict[move_poke_type].get(enemy_poke_type, 2)


def can_effect(move_poke_type, enemy_poke):
    return get_type_match_x2(move_poke_type, enemy_poke.type1) * get_type_match_x2(move_poke_type, enemy_poke.type2) > 0


def friend_type_bonus_x2(move_poke_type, friend_poke):
    """
    タイプ一致ボーナス(2倍した値を返す)
    """
    if move_poke_type is PokeType.Empty:
        # こんらん用
        return 2
    return 3 if move_poke_type in [friend_poke.type1, friend_poke.type2] else 2
