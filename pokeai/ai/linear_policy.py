import numpy as np
from logging import getLogger
from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.policy_model import PolicyModel
from pokeai.ai.random_policy import RandomPolicy

logger = getLogger(__name__)


class LinearPolicy(RandomPolicy):
    """
    線形モデル方策
    """
    feature_extractor: FeatureExtractor
    softmax_temp: float  # softmax温度。大きいほどランダムに近づく。0ならばスコア最大値の方策を常に選択
    model: PolicyModel

    def __init__(self, feature_extractor: FeatureExtractor, model: PolicyModel, softmax_temp=1.0):
        """
        方策のコンストラクタ
        :param feature_extractor:
        :param model: (N, F)行列を与えると(N, A)行列が出てくるような関数、N=バッチサイズ(現状1)、F=特徴次元、A=行動次元(3vs3なら18)
        :param softmax_temp:
        """
        super().__init__()
        self.feature_extractor = feature_extractor
        self.softmax_temp = softmax_temp
        self.model = model

    def choice_turn_start(self, battle_status: BattleStatus, request: dict) -> str:
        """
        ターン開始時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"move [1-4]|switch [1-6]"
        """
        active = request['active']
        if active[0].get('trapped'):
            # あなをほるなど特定の技の発動中で、それを選ぶほかない
            return 'move 1'
        choice_idxs, choice_keys = self._get_possible_actions(request, False)
        if len(choice_idxs) == 1:
            return choice_keys[0]
        return self._choice_by_model(battle_status, choice_idxs, choice_keys)

    def choice_force_switch(self, battle_status: BattleStatus, request: dict) -> str:
        """
        強制交換時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"switch [1-6]"
        """
        choice_idxs, choice_keys = self._get_possible_actions(request, True)
        if len(choice_idxs) == 1:
            return choice_keys[0]
        return self._choice_by_model(battle_status, choice_idxs, choice_keys)

    def _choice_by_model(self, battle_status: BattleStatus, choice_idxs, choice_keys):
        """
        モデルで各行動の優先度を出し、それに従い行動を選択する
        :param battle_status:
        :param choice_idxs:
        :param choice_keys:
        :return:
        """
        logger.info(f"choice of player {battle_status.side_friend}")
        feat = self.feature_extractor.transform(battle_status)
        logger.debug(f"feature: {feat.tolist()}")
        # modelは一応バッチ方向入力を想定している
        action_logits = self.model(feat[np.newaxis, :])[0, :]
        possible_choice_logits = action_logits[choice_idxs]
        possible_choice_probs = self._softmax_with_temp(possible_choice_logits)
        # 確率に従って行動を選択
        idx = int(np.random.choice(len(possible_choice_probs), p=possible_choice_probs))
        chosen = choice_keys[idx]
        logger.debug(f"choices_probs: {dict(zip(choice_keys, possible_choice_probs))}, chosen: {chosen}")
        return chosen

    def _softmax_with_temp(self, vec: np.ndarray):
        """
        ベクトルの温度つきsoftmaxをとる
        :param vec:
        :return:
        """
        if self.softmax_temp <= 0.0:
            # 最大値を1とするベクトル
            softmax = np.zeros_like(vec)
            softmax[np.argmax(vec)] = 1.0
        else:
            ofs = np.max(vec)
            exp = np.exp((vec - ofs) / self.softmax_temp)
            softmax = exp / np.sum(exp)
        return softmax

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
        for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
            if backpokemon['active']:
                # 場に出ている
                active_poke_idx = i
                continue
            if backpokemon['condition'].endswith(' fnt'):
                # 瀕死状態
                continue
            if force_switch:
                choice_idxs.append(i * 6 + 5)
                choice_keys.append(f'switch {i + 1}')  # 1-origin index
            else:
                choice_idxs.append(i * 6 + 4)
                choice_keys.append(f'switch {i + 1}')  # 1-origin index
        assert active_poke_idx is not None
        if not force_switch:
            active = request['active']
            assert not active[0].get('trapped')
            for i, move in enumerate(active[0]['moves']):
                if not move.get('disabled'):
                    choice_idxs.append(active_poke_idx * 6 + i)
                    choice_keys.append(f'move {i + 1}')  # 1-origin index
        assert len(choice_idxs) > 0
        return choice_idxs, choice_keys
