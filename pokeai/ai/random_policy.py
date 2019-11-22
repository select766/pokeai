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
        choice_idxs, choice_keys = self._get_possible_actions(request, False)
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
        choice_idxs, choice_keys = self._get_possible_actions(request, True)
        if len(choice_keys) > 1:
            return random.choice(choice_keys)
        else:
            return choice_keys[0]

    def _get_possible_actions(self, request: dict, force_switch: bool):
        """
        取れる行動の番号およびそれを表す文字列を返す
        :param request:
        :return:
        """

        """
        出力ベクトルの各次元と行動の関係
        X番目のポケモン(X=0~5)
        6X+0~3: 技0~3
        6X+4: このポケモンに交代
        6X+5: 強制交換の時このポケモンを出す
        """
        active_poke_idx = None
        choice_idxs = []
        choice_keys = []
        if not force_switch:
            active = request['active']
            trapped = active[0].get('trapped')  # 交換不可状態
        else:
            active = None
            trapped = False

        # ゴッドバードなど複数ターン継続する技では、
        # [{"moves":[{"move":"Sky Attack","id":"skyattack"}],"trapped":true}],
        # のようにmoveが１要素だけになり、active.trapped:trueとなる
        # moveの番号自体ずれる(固定された技を強制選択となり"move 1"を返すこととなる)ので、番号と技の対応に注意

        for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
            if backpokemon['active']:
                # 場に出ている
                active_poke_idx = i
                continue
            if backpokemon['condition'].endswith(' fnt'):
                # 瀕死状態
                continue
            if not trapped:
                if force_switch:
                    choice_idxs.append(i * 6 + 5)
                    choice_keys.append(f'switch {i + 1}')  # 1-origin index
                else:
                    choice_idxs.append(i * 6 + 4)
                    choice_keys.append(f'switch {i + 1}')  # 1-origin index
        assert active_poke_idx is not None
        if not force_switch:
            for i, move in enumerate(active[0]['moves']):
                if not move.get('disabled'):
                    choice_idxs.append(active_poke_idx * 6 + i)
                    choice_keys.append(f'move {i + 1}')  # 1-origin index
        assert len(choice_idxs) > 0
        return choice_idxs, choice_keys
