# -*- coding:utf-8 -*-

from enum import Enum, auto
from .poke import Poke
from .field_action import FieldActionBegin, FieldActionBeginCommand
from .battle_rng import BattleRng, BattleRngReason
from .field_log import FieldLog, FieldLogReason, FieldLogSender
from .move_calculator import MoveCalculator


class Field(object):
    def __init__(self, parties):
        self.parties = parties  # List[Party]
        self.turn_number = 0
        self.phase = FieldPhase.Begin
        self.rng = None
        self.logger = None

        self.actions_begin = None
        self.actions_faint_change = None
        self.first_player = 0
        self.move_calculator = MoveCalculator(self)

    def step(self):
        if self.phase is FieldPhase.Begin:
            self.phase = self.step_begin()
        elif self.phase is FieldPhase.FirstMove:
            self.phase = self.step_first_move()
        elif self.phase is FieldPhase.FirstPC:
            self.phase = self.step_first_pc()
        elif self.phase is FieldPhase.SecondMove:
            self.phase = self.step_second_move()
        elif self.phase is FieldPhase.SecondPC:
            self.phase = self.step_second_pc()
        elif self.phase is FieldPhase.FaintChange:
            self.phase = self.step_faint_change()
        elif self.phase is FieldPhase.EndTurn:
            self.phase = self.step_end_turn()
        else:
            raise NotImplementedError()

        return self.phase

    def step_begin(self):
        self._log_msg("ターン {}".format(self.turn_number))
        speeds = []
        # 先攻決め
        for player in [0, 1]:
            speed = self._get_fighting_poke(player).eff_s()
            if self.actions_begin[player].command is FieldActionBeginCommand.Change:
                # 交代は先攻
                speed += 10000
            speeds.append(speed)

        orig_speeds = [speeds[0], speeds[1]]
        speed_rnd = self.rng.get(0, BattleRngReason.MoveOrder, top=1)
        if speeds[0] == speeds[1]:
            speeds[0] += speed_rnd

        if speeds[0] > speeds[1]:
            self.first_player = 0
        else:
            self.first_player = 1

        self.logger.write(FieldLog(FieldLogSender.Field, FieldLogReason.MoveOrder,
                                   {"speeds": orig_speeds, "first_player": self.first_player}, "Speeds: {}, first_player: {}".format(orig_speeds, self.first_player)))

        return FieldPhase.FirstMove

    def step_first_move(self):
        return self.move_calculator.step_x_move(0)

    def step_first_pc(self):
        return self.move_calculator.step_x_pc(0)

    def step_second_move(self):
        return self.move_calculator.step_x_move(1)

    def step_second_pc(self):
        return self.move_calculator.step_x_pc(1)

    def step_faint_change(self):
        for player in [0, 1]:
            action = self.actions_faint_change[player]
            if self._get_fighting_poke(player).is_faint:
                self.parties[player].change_fighting_poke(action.change_idx)
                self._log_msg("Player {}は{}を繰り出した".format(
                    player, self._get_fighting_poke(player)))
            else:
                assert action is None
        return FieldPhase.EndTurn

    def step_end_turn(self):
        self.turn_number += 1
        self.actions_begin = None
        self.actions_faint_change = None

        return FieldPhase.Begin

    def _log_msg(self, message):
        self.logger.write(FieldLog(FieldLogSender.Field,
                                   FieldLogReason.Empty, None, message))

    def get_winner(self):
        """
        phase == FieldPhase.GameEnd のとき、勝ったプレイヤーを取得する
        """
        # TODO: じばくによる負け、どく等で同時に倒れた場合
        for player in [0, 1]:
            if self.parties[player].is_all_faint():
                return 1 - player
        return None

    def set_actions_begin(self, actions):
        self.actions_begin = actions

    def set_actions_faint_change(self, actions):
        self.actions_faint_change = actions

    def _get_fighting_poke(self, player):
        return self.parties[player].get_fighting_poke()


class FieldPhase(Enum):
    Begin = 1
    FirstMove = 2
    FirstPC = 3
    SecondMove = 4
    SecondPC = 5
    FaintChange = 6
    EndTurn = 7
    GameEnd = 8
