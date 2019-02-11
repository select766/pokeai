"""
強化学習による学習済みエージェント
"""

from typing import Optional

from bson import ObjectId
from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_observer import BattleObserver
from pokeai.sim import Field
from pokeai.sim.field_action import FieldAction
from pokeai.sim.party_template import PartyTemplate
import pokeai.agent.agent_builder


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

    def get_action(self, field: Field, player: int) -> Optional[FieldAction]:
        action_objs = self.observer.get_field_action_map(field, player)
        if len(action_objs) > 0:
            action = self.agent.act(self.observer.make_observation(field, player))
            action_obj, _ = self.observer.get_field_action(field, player, action)
            return action_obj
        else:
            # 瀕死で相手だけ交代が必要な場面
            return None
