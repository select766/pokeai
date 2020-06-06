from typing import NamedTuple

from pokeai.ai.battle_status import BattleStatus


class RLPolicyObservation(NamedTuple):
    battle_status: BattleStatus
    request: dict
