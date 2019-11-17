import random

from pokeai.ai.action_policy import ActionPolicy
from pokeai.ai.battle_status import BattleStatus


class RandomPolicy(ActionPolicy):
    def __init__(self, switch_prob: float = 0.2):
        """
        ランダム行動の初期化
        :param switch_prob: 技と交換の両方が選べる状況において、交換を選ぶ確率
        """
        self.switch_prob = switch_prob

    def choice_turn_start(self, battle_status: BattleStatus, request: dict) -> str:
        """
        ターン開始時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"move [1-4]|switch [1-6]"
        """
        active = request['active']
        assert len(active) == 1  # シングルバトル
        move_choices = []
        for i, move in enumerate(active[0]['moves']):
            if not move.get('disabled'):
                move_choices.append(f'move {i + 1}')  # 1-origin index

        # ゴッドバードなど複数ターン継続する技では、
        # [{"moves":[{"move":"Sky Attack","id":"skyattack"}],"trapped":true}],
        # のようにmoveが１要素だけになり、active.trapped:trueとなる
        # moveの番号自体ずれる(固定された技を強制選択となり"move 1"を返すこととなる)ので、番号と技の対応に注意
        switch_choices = []
        if not active[0].get('trapped'):
            for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
                if backpokemon['active']:
                    # 場に出ている
                    continue
                if backpokemon['condition'].endswith(' fnt'):
                    # 瀕死状態
                    continue
                switch_choices.append(f"switch {i + 1}")  # 1-origin index

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
        forceSwitch = request['forceSwitch']
        assert len(forceSwitch) == 1  # シングルバトル
        assert forceSwitch[0]
        switch_choices = []
        for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
            if backpokemon['active']:
                # 場に出ている
                continue
            if backpokemon['condition'].endswith(' fnt'):
                # 瀕死状態
                continue
            switch_choices.append(f"switch {i + 1}")  # 1-origin index
        assert len(switch_choices) > 0
        return random.choice(switch_choices)
