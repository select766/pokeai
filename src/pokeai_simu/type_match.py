# -*- coding:utf-8 -*-

"""
タイプ相性計算
"""

from .poke_type import PokeType
from .poke import Poke


def get_type_match_x2(move_poke_type, enemy_poke_type):
    """
    単一のタイプ相性計算
    """
    # TODO
    return 2


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
