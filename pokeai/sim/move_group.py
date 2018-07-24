"""
技グループの定義
技グループは、フラグ部分（タイプ・威力・命中・PP）以外同じ効果を持つ技のリスト。
"""
from typing import List, Dict
from enum import Enum, auto
from pokeai.sim.move import Move


class MoveGroupName(Enum):
    SIMPLE = auto()
    SPLASH = auto()
    HYPERBEAM = auto()
    FLINCH_10 = auto()
    FLINCH_30 = auto()
    DIG = auto()


move_group = {
    # 通常攻撃技
    MoveGroupName.SIMPLE: [Move.CUT, Move.DRILLPECK, Move.EARTHQUAKE, Move.EGGBOMB, Move.GUST, Move.HORNATTACK,
                           Move.HYDROPUMP, Move.MEGAKICK, Move.MEGAPUNCH, Move.PAYDAY, Move.PECK, Move.POUND,
                           Move.ROCKSLIDE, Move.ROCKTHROW, Move.SCRATCH, Move.SLAM, Move.STRENGTH, Move.SURF,
                           Move.TACKLE, Move.VICEGRIP, Move.VINEWHIP, Move.WATERFALL, Move.WATERGUN, Move.WINGATTACK, ],
    MoveGroupName.SPLASH: [Move.ROAR, Move.SPLASH, Move.TELEPORT, Move.WHIRLWIND],
    MoveGroupName.HYPERBEAM: [Move.HYPERBEAM],
    MoveGroupName.FLINCH_10: [Move.BONECLUB, Move.HYPERFANG],
    MoveGroupName.FLINCH_30: [Move.BITE, Move.HEADBUTT, Move.LOWKICK, Move.ROLLINGKICK, Move.STOMP],
    MoveGroupName.DIG: [Move.DIG, Move.FLY],
}  # type: Dict[MoveGroupName, List[Move]]
