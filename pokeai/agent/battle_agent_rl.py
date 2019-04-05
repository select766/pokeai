"""
強化学習による学習済みエージェント
"""

from typing import Optional

from bson import ObjectId
from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_observer import BattleObserver
from pokeai.sim import Field
from pokeai.sim.field_action import FieldAction
from pokeai.sim.field_record import FieldRecord, FieldRecordReason
from pokeai.sim.party_template import PartyTemplate
import pokeai.agent.agent_builder


class AgentDummyLogger:
    """
    ChainerRLのAgent内でself.logger.debug(msg)されたメッセージを受け取りFieldLogとして書き出すオブジェクト
    """

    def __init__(self):
        self.print_func = None

    def debug(self, msg, *args):
        if self.print_func is not None:
            formatted_msg = msg % args
            self.print_func(FieldRecord(FieldRecordReason.OTHER, None, formatted_msg))


class BattleAgentRl(BattleAgent):
    def __init__(self, agent_id: ObjectId, party_t: PartyTemplate, observer: BattleObserver,
                 params, model_dump_dir: str):
        self.agent_id = agent_id
        self.party_t = party_t
        self.observer = observer
        self.params = params
        self.model_dump_dir = model_dump_dir

        self.agent = pokeai.agent.agent_builder.build(params, observer)

        self.agent.load(self.model_dump_dir)

        self._dummy_logger = AgentDummyLogger()
        self.agent.logger = self._dummy_logger

    def get_action(self, field: Field, player: int, logger=None) -> Optional[FieldAction]:
        action_objs = self.observer.get_field_action_map(field, player)
        self._dummy_logger.print_func = logger
        if len(action_objs) > 0:
            action = self.agent.act(self.observer.make_observation(field, player))
            action_obj, _ = self.observer.get_field_action(field, player, action)
            return action_obj
        else:
            # 瀕死で相手だけ交代が必要な場面
            return None
