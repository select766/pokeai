from typing import NamedTuple, List

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.common import PossibleAction


class RLPolicyObservation(NamedTuple):
    battle_status: BattleStatus
    request: dict
    possible_actions: List[PossibleAction]
