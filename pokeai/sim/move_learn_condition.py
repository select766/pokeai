from enum import Enum

from pokeai.sim.move import Move


class MoveLearnType(Enum):
    LV = 1
    TM = 2


class MoveLearnCondition:
    """
    ポケモンが覚える技とその条件
    """
    move: Move
    move_learn_type: MoveLearnType
    lv: int  # レベルアップ以外で覚える場合は0とする

    def __init__(self, move: Move, move_learn_type: MoveLearnType, lv: int):
        self.move = move
        self.move_learn_type = move_learn_type
        self.lv = lv
