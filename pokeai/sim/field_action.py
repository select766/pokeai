from enum import Enum


class FieldActionType(Enum):
    MOVE = 1
    CHANGE = 2
    FAINT_CHANGE = 3


class FieldAction:
    """
    プレイヤーの1回の行動選択を表す
    """
    action_type: FieldActionType
    move_idx: int
    change_idx: int
    faint_change_idx: int

    def __init__(self, action_type: FieldActionType, *,
                 move_idx: int = 0,  # キーワード指定必須
                 change_idx: int = 0,
                 faint_change_idx: int = 0):
        self.action_type = action_type
        self.move_idx = move_idx
        self.change_idx = change_idx
        self.faint_change_idx = faint_change_idx
