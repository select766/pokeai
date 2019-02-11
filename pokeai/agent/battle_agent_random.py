"""
ランダムに行動するエージェント
"""
import random
from typing import Optional

from bson import ObjectId
from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_observer import BattleObserver
from pokeai.sim import Field
from pokeai.sim.field_action import FieldAction
from pokeai.sim.party_template import PartyTemplate


class BattleAgentRandom(BattleAgent):
    def __init__(self, agent_id: ObjectId, party_t: PartyTemplate, observer: BattleObserver):
        self.agent_id = agent_id
        self.party_t = party_t
        self.observer = observer

    def get_action(self, field: Field, player: int) -> Optional[FieldAction]:
        action_objs = self.observer.get_field_action_map(field, player)
        if len(action_objs) > 0:
            return random.choice(list(action_objs.values()))
        else:
            # 瀕死で相手だけ交代が必要な場面
            return None
