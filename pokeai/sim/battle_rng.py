# -*- coding:utf-8 -*-

import random
from enum import Enum, auto


class BattleRng(object):
    def __init__(self):
        pass

    def get(self, player, reason):
        pass


class BattleRngRandom(BattleRng):
    def __init__(self, seed=None):
        super().__init__()
        self._rng = random.Random(seed)

    def get(self, player, reason, top=255):
        return self._rng.randint(0, top)


class BattleRngReason(Enum):
    MoveOrder = auto()
    Hit = auto()
    Critical = auto()
    DamageRandom = auto()
    Paralysis = auto()
    Confusion = auto()
    ConfusionTurn = auto()
    SleepTurn = auto()
    SideEffect = auto()
