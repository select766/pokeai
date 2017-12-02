# -*- coding:utf-8 -*-

from .poke_type import PokeType


class PokeStaticParam(object):
    """description of class"""

    def __init__(self):
        self.dexno = 0
        self.move_ids = []
        self.type1 = PokeType.Empty
        self.type2 = PokeType.Empty
        self.max_hp = 0
        self.st_a = 0
        self.st_b = 0
        self.st_c = 0
        self.st_s = 0
        self.base_s = 0
        self.level = 50
