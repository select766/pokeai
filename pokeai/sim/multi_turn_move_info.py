from typing import Callable, Optional

from pokeai.sim.move import Move
from pokeai.sim.poke import Poke


class MultiTurnMoveInfo:
    """
    複数ターン連続する技の状態
    """
    move: Move
    remaining_turns: int
    on_abort: Optional[Callable[[Poke], None]]

    def __init__(self, move: Move, on_abort: Optional[Callable[[Poke], None]]):
        self.move = move
        self.on_abort = on_abort

    def abort(self, attack_poke: Poke):
        """
        技が発動できず中止した場合に呼び出される。
        :param attack_poke:
        :return:
        """
        if self.on_abort is not None:
            self.on_abort(attack_poke)
