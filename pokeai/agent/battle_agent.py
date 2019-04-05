"""
ポケモンバトルの行動を選択するエージェントの定義
"""
from bson import ObjectId
from pokeai.sim import Field
from pokeai.sim.field_action import FieldAction
from pokeai.sim.party_template import PartyTemplate


class BattleAgent:
    agent_id: ObjectId
    party_t: PartyTemplate

    def get_action(self, field: Field, player: int, logger=None) -> FieldAction:
        raise NotImplementedError
