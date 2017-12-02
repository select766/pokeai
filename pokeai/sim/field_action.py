# -*- coding:utf-8 -*-

import enum


class FieldActionBeginCommand(enum.Enum):
    Move = 1
    Change = 2


class FieldActionBegin(object):
    def __init__(self, command, move_idx, change_idx):
        self.command = command
        self.move_idx = move_idx
        self.change_idx = change_idx

    @classmethod
    def move(cls, move_idx):
        return cls(FieldActionBeginCommand.Move, move_idx, 0)

    @classmethod
    def change(cls, change_idx):
        return cls(FieldActionBeginCommand.Change, 0, change_idx)


class FieldActionFaintChange(object):
    def __init__(self, change_idx):
        self.change_idx = change_idx
