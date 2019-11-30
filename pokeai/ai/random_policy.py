import random

from pokeai.ai.action_policy import ActionPolicy
from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import get_possible_actions


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
        choice_idxs, choice_keys, _ = get_possible_actions(battle_status, request)
        switch_choices = []
        move_choices = []
        for ck in choice_keys:
            if ck.startswith("switch"):
                switch_choices.append(ck)
            elif ck.startswith("move"):
                move_choices.append(ck)
            else:
                raise NotImplementedError

        if len(switch_choices) > 0 and (len(move_choices) == 0 or random.random() < self.switch_prob):
            # 交換しかできない場合か、両方できる場合で一定確率で交換を選ぶ
            return random.choice(switch_choices)
        else:
            assert len(move_choices) > 0
            return random.choice(move_choices)

    def choice_force_switch(self, battle_status: BattleStatus, request: dict) -> str:
        """
        強制交換時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"switch [1-6]"
        """
        # TODO: バトンタッチ対応
        choice_idxs, choice_keys, _ = get_possible_actions(battle_status, request)
        if len(choice_keys) > 1:
            return random.choice(choice_keys)
        else:
            return choice_keys[0]
