from typing import Callable
from pokeai.sim.poke_db_move_flag import PokeDBMoveFlag


class PokeDBMoveInfo:
    """
    技のパラメータおよび判定処理
    """
    flag: PokeDBMoveFlag
    check_hit: Callable
    launch_move: Callable
    check_side_effect: Callable
    launch_side_effect: Callable

    def __init__(self, flag: PokeDBMoveFlag,
                 check_hit: Callable,
                 launch_move: Callable,
                 check_side_effect: Callable,
                 launch_side_effect: Callable,
                 ):
        self.flag = flag
        self.check_hit = check_hit
        self.launch_move = launch_move
        self.check_side_effect = check_side_effect
        self.launch_side_effect = launch_side_effect
