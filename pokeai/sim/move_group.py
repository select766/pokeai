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


move_group = {
    # 通常攻撃技
    MoveGroupName.SIMPLE: [Move.CUT, Move.DRILLPECK, Move.EARTHQUAKE, Move.EGGBOMB, Move.GUST, Move.HORNATTACK,
                           Move.HYDROPUMP, Move.MEGAKICK, Move.MEGAPUNCH, Move.PAYDAY, Move.PECK, Move.POUND,
                           Move.ROCKTHROW, Move.SCRATCH, Move.SLAM, Move.STRENGTH, Move.SURF, Move.TACKLE,
                           Move.VICEGRIP, Move.VINEWHIP, Move.WATERFALL, Move.WATERGUN, Move.WINGATTACK, ],
    MoveGroupName.SPLASH: [Move.ROAR, Move.SPLASH, Move.TELEPORT, Move.WHIRLWIND],
}  # type: Dict[MoveGroupName, List[Move]]
