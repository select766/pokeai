# -*- coding:utf-8 -*-

"""
技の発動・ダメージ計算
"""

from enum import Enum, auto
from .poke_type import PokeType
from .poke import Poke, PokeNVCondition
from .field_action import FieldActionBegin, FieldActionBeginCommand
from .battle_rng import BattleRng, BattleRngReason
from .field_log import FieldLog, FieldLogReason, FieldLogSender
from .move_table import MoveTable

Field = FieldPhase = None


class MoveCalculator(object):
    def __init__(self, field):
        _import()
        self.field = field

    def step_x_move(self, move_order):
        friend_player = self.field.first_player ^ move_order
        enemy_player = 1 - friend_player

        action = self.field.actions_begin[friend_player]
        if action.command is FieldActionBeginCommand.Change:
            # 任意交代
            self.field.parties[friend_player].change_fighting_poke(
                action.change_idx)
            self._log_msg("Player {}は{}を繰り出した".format(
                friend_player, self.field._get_fighting_poke(friend_player)))
        else:
            # 技
            friend_poke = self.field._get_fighting_poke(friend_player)
            enemy_poke = self.field._get_fighting_poke(enemy_player)
            move_idx = self.field.actions_begin[friend_player].move_idx
            move_id = friend_poke.static_param.move_ids[move_idx]
            move_entry = MoveTable.get(move_id)
            self._log_msg("Player {}の技 {}".format(friend_player, move_id))
            self.calc_move(move_order, friend_player,
                           friend_poke, enemy_poke, move_entry)
        return self._next_step_or_faint_change([FieldPhase.FirstPC, FieldPhase.SecondPC][move_order])

    def calc_move(self, move_order, friend_player, friend_poke, enemy_poke, move_entry):
        """
        技の発動・ダメージ計算コア
        """
        handler = friend_poke.move_handler
        if handler is None:
            handler = move_entry.move_handler(self.field, move_entry)
            friend_poke.move_handler = handler
        else:
            # 連続技の２回目以降
            self._log_msg("連続技の2回目以降")

        handler.run(move_order, friend_player, friend_poke, enemy_poke)

        if not handler.is_continuing():
            # 技の発動が完了
            friend_poke.move_handler = None
        else:
            self._log_msg("次ターンも連続技発動")

    def step_x_pc(self, move_order):
        friend_player = self.field.first_player ^ move_order
        enemy_player = 1 - friend_player

        friend_poke = self.field._get_fighting_poke(friend_player)
        # TODO: やどりぎ
        if friend_poke.nv_condition is PokeNVCondition.Poison:
            poison_ratio = 1
            if friend_poke.bad_poison:
                friend_poke.bad_poison_turn = min(
                    friend_poke.bad_poison_turn + 1, 15)
                poison_ratio = friend_poke.bad_poison_turn
            self._log_msg("どくのダメージを受けている")
            poison_damage = friend_poke.calc_ratio_damage(poison_ratio)
            friend_poke.hp -= poison_damage

        if friend_poke.nv_condition is PokeNVCondition.Burn:
            self._log_msg("やけどのダメージを受けている")
            burn_damage = friend_poke.calc_ratio_damage(1)
            friend_poke.hp -= burn_damage

        return self._next_step_or_faint_change([FieldPhase.SecondMove, FieldPhase.EndTurn][move_order])

    def _next_step_or_faint_change(self, ordinary_phase):
        """
        ポケモンがひんしなら交代フェーズ、そうでなければ引数のフェーズを返す
        """
        game_end = False
        faint_change = False
        for player in [0, 1]:
            player_poke = self.field._get_fighting_poke(player)
            if player_poke.is_faint:
                self._log_msg("Player {}の{}はたおれた".format(player, player_poke))
                if self.field.parties[player].is_all_faint:
                    game_end = True
                else:
                    faint_change = True
        if game_end:
            return FieldPhase.GameEnd
        if faint_change:
            return FieldPhase.FaintChange
        return ordinary_phase

    def _log_msg(self, message):
        self.field.logger.write(
            FieldLog(FieldLogSender.MoveCalculator, FieldLogReason.Empty, None, message))


def _import():
    global FieldPhase
    global Field
    from .field import Field, FieldPhase
