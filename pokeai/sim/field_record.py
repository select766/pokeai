from enum import Enum, auto


class FieldRecordReason(Enum):
    """
    記録の理由
    """
    OTHER = auto()


class FieldRecord:
    """
    シミュレータ内の動作の記録（棋譜）
    """
    reason: FieldRecordReason
    data: object
    message: str

    def __init__(self, reason: FieldRecordReason, data: object, message: str):
        self.reason = reason
        self.data = data
        self.message = message

    def __str__(self):
        return f"{self.reason.name}:{self.message}"
