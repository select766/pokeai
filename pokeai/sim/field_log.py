# -*- coding:utf-8 -*-

from enum import Enum, auto


class FieldLog(object):
    def __init__(self, sender, reason, data, message):
        self.sender = sender
        self.reason = reason
        self.data = data
        self.message = message

    def __str__(self):
        return "{}:{}:{}".format(self.sender.name, self.reason.name, self.message)


class FieldLogger(object):
    def __init__(self):
        pass

    def write(self, log):
        pass


class FieldLoggerPrint(FieldLogger):
    def __init__(self):
        super().__init__()

    def write(self, log):
        print(str(log))


class FieldLoggerBuffer(FieldLogger):
    def __init__(self):
        super().__init__()
        self.buffer = []

    def write(self, log):
        self.buffer.append(log)


class FieldLogSender(Enum):
    Empty = auto()
    Field = auto()
    MoveCalculator = auto()
    MoveHandler = auto()


class FieldLogReason(Enum):
    Empty = auto()
    MoveOrder = auto()
