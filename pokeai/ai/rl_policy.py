import json
import logging
from logging import getLogger

from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import get_possible_actions
from pokeai.ai.state_feature_extractor import StateFeatureExtractor
from pokeai.ai.random_policy import RandomPolicy
from pokeai.ai.rl_policy_observation import RLPolicyObservation

logger = getLogger(__name__)


class RLPolicy(RandomPolicy):
    """
    強化学習による方策
    """
    feature_extractor: StateFeatureExtractor
    agent: Agent

    def __init__(self, agent: Agent):
        """
        方策のコンストラクタ
        """
        super().__init__()
        self.agent = agent

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

    def _choice_by_model(self, battle_status: BattleStatus, request: dict) -> str:
        """
        モデルで各行動の優先度を出し、それに従い行動を選択する
        :param battle_status:
        :param choice_idxs:
        :param choice_keys:
        :return:
        """
        logger.debug(f"choice of player {battle_status.side_friend}")
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
        action = self.agent.act(obs, 0.0)  # TODO: バトルの進行による補助的な報酬
        chosen = possible_actions[action]
        logger.debug(f"chosen: {chosen}")
        return chosen.simulator_key

    def game_end(self, reward: float):
        self.agent.stop_episode(reward)
