import json
import logging
from logging import getLogger
from typing import Optional

from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import get_possible_actions
from pokeai.ai.state_feature_extractor import StateFeatureExtractor
from pokeai.ai.random_policy import RandomPolicy
from pokeai.ai.rl_policy_observation import RLPolicyObservation
from pokeai.ai.surrogate_reward_config import SurrogateRewardConfig

logger = getLogger(__name__)


class RLPolicy(RandomPolicy):
    """
    強化学習による方策
    """
    feature_extractor: StateFeatureExtractor
    agent: Agent
    surrogate_reward_config: SurrogateRewardConfig
    last_reward_potential: Optional[float]

    def __init__(self, agent: Agent, surrogate_reward_config: SurrogateRewardConfig):
        """
        方策のコンストラクタ
        """
        super().__init__()
        self.agent = agent
        self.surrogate_reward_config = surrogate_reward_config
        self.last_reward_potential = None

    def game_start(self):
        """
        内部状態のリセット
        :return:
        """
        self.last_reward_potential = None

    def choice_turn_start(self, battle_status: BattleStatus, request: dict) -> str:
        """
        ターン開始時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"move [1-4]|switch [1-6]"
        """
        return self._choice_by_model(battle_status, request)

    def choice_force_switch(self, battle_status: BattleStatus, request: dict) -> str:
        """
        強制交換時の行動選択
        :param battle_status:
        :param request:
        :return: 行動。"switch [1-6]"
        """
        return self._choice_by_model(battle_status, request)

    def _calc_reward_potential(self, battle_status: BattleStatus) -> float:
        """
        HP率などから計算した、自分側が有利なら大きな値になるポテンシャル値
        :param battle_status:
        :return:
        """
        sps = []
        for side in [battle_status.side_friend, battle_status.side_opponent]:
            ss = battle_status.side_statuses[side]
            side_potential = ss.get_mean_hp_ratio() * self.surrogate_reward_config.hp_ratio + ss.get_alive_ratio() * self.surrogate_reward_config.alive_ratio
            sps.append(side_potential)
        if self.surrogate_reward_config.only_opponent:
            return -sps[1]
        else:
            return sps[0] - sps[1]

    def _choice_by_model(self, battle_status: BattleStatus, request: dict) -> str:
        """
        モデルで各行動の優先度を出し、それに従い行動を選択する
        :param battle_status:
        :param choice_idxs:
        :param choice_keys:
        :return:
        """
        logger.debug(f"choice of player {battle_status.side_friend}")
        reward_potential = self._calc_reward_potential(battle_status)
        possible_actions = get_possible_actions(battle_status, request)
        if len(possible_actions) == 1:
            # 選択肢が１つだけの場合はモデルに与えない
            # 与える場合、action番号を正しく設定する必要あり(get_possible_actions内コメントに注意)
            logger.debug(f"only one choice: {possible_actions[0]}")
            return possible_actions[0].simulator_key
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                'possible_actions: ' + json.dumps([pa._asdict() for pa in possible_actions]))
        obs = RLPolicyObservation(battle_status, request, possible_actions)
        if self.last_reward_potential is not None:
            surrogate_reward = reward_potential - self.last_reward_potential
        else:
            surrogate_reward = 0.0
        logger.debug(f"surrogate_reward: {surrogate_reward}")
        action = self.agent.act(obs, surrogate_reward)
        self.last_reward_potential = reward_potential
        chosen = possible_actions[action]
        logger.debug(f"chosen: {chosen}")
        return chosen.simulator_key

    def game_end(self, reward: float):
        # 厳密には最終ターンのダメージで補助報酬を与えるべきかもしれない
        if self.surrogate_reward_config.offset_at_end:
            # 今までに与えた補助報酬をキャンセルし、ゲーム全体の報酬和は勝敗（この関数の引数）だけとする
            reward = reward - self.last_reward_potential
        self.agent.stop_episode(reward)
