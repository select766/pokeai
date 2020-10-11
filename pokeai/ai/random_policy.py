import json
import random
import logging
from logging import getLogger

from pokeai.ai.action_policy import ActionPolicy
from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import get_possible_actions

logger = getLogger(__name__)


class RandomPolicy(ActionPolicy):
    def __init__(self, switch_prob: float = 0.2):
        """
        ランダム行動の初期化
        :param switch_prob: 技と交換の両方が選べる状況において、交換を選ぶ確率
        """
        super().__init__()
        self.switch_prob = switch_prob

    def choice_turn_start(self, battle_status: BattleStatus, request: dict) -> str:
        """
        ターン開始時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"move [1-4]|switch [1-6]"
        """
        possible_actions = get_possible_actions(battle_status, request)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                'policy_choice_turn_start: ' + json.dumps([pa._asdict() for pa in possible_actions]))
        switch_choices = []
        move_choices = []
        for ck in possible_actions:
            if ck.switch:
                switch_choices.append(ck)
            else:
                move_choices.append(ck)

        if len(switch_choices) > 0 and (len(move_choices) == 0 or random.random() < self.switch_prob):
            # 交換しかできない場合か、両方できる場合で一定確率で交換を選ぶ
            return random.choice(switch_choices).simulator_key
        else:
            assert len(move_choices) > 0
            return random.choice(move_choices).simulator_key

    def choice_force_switch(self, battle_status: BattleStatus, request: dict) -> str:
        """
        強制交換時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"switch [1-6]"
        """
        # TODO: バトンタッチ対応
        possible_actions = get_possible_actions(battle_status, request)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                'policy_choice_force_switch: ' + json.dumps([pa._asdict() for pa in possible_actions]))
        if len(possible_actions) > 1:
            return random.choice(possible_actions).simulator_key
        else:
            return possible_actions[0].simulator_key
