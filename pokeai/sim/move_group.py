"""
技グループの定義
技グループは、フラグ部分（タイプ・威力・命中・PP）以外同じ効果を持つ技のリスト。
"""
from typing import List, Dict
from enum import Enum, auto
from pokeai.sim.move import Move


class MoveGroupName(Enum):
    SIMPLE = auto()
    SWIFT = auto()
    QUICKATTACK = auto()
    SPLASH = auto()
    HYPERBEAM = auto()
    FLINCH_10 = auto()
    FLINCH_30 = auto()
    DIG = auto()
    BLIZZARD = auto()
    FREEZE_10 = auto()
    PARALYSIS_10 = auto()
    PARALYSIS_30 = auto()
    BODYSLAM = auto()
    BURN_10 = auto()
    BURN_30 = auto()
    POISON_20 = auto()
    POISON_40 = auto()
    HYPNOSIS = auto()
    TOXIC = auto()
    POISONGAS = auto()
    GLARE = auto()
    THUNDERWAVE = auto()
    CRITICAL = auto()
    EVASION_UP = auto()
    A_UP = auto()
    A_UP2 = auto()
    B_UP = auto()
    B_UP2 = auto()
    C_UP = auto()
    C_UP2 = auto()
    S_UP2 = auto()
    ACCURACY_DOWN = auto()
    A_DOWN = auto()
    B_DOWN = auto()
    B_DOWN2 = auto()
    S_DOWN = auto()
    CONFUSE = auto()
    SIDE_A_DOWN = auto()
    SIDE_B_DOWN = auto()
    SIDE_C_DOWN = auto()
    SIDE_S_DOWN = auto()
    SIDE_CONFUSE = auto()
    CONST_20 = auto()
    CONST_40 = auto()
    FISSURE = auto()
    EXPLOSION = auto()
    LEECHSEED = auto()


move_group = {
    # 通常攻撃技
    MoveGroupName.SIMPLE: [Move.CUT, Move.DIZZYPUNCH, Move.DRILLPECK, Move.EARTHQUAKE, Move.EGGBOMB, Move.GUST,
                           Move.HORNATTACK, Move.HYDROPUMP, Move.MEGAKICK, Move.MEGAPUNCH, Move.PAYDAY, Move.PECK,
                           Move.POUND, Move.ROCKSLIDE, Move.ROCKTHROW, Move.SCRATCH, Move.SLAM, Move.STRENGTH,
                           Move.SURF, Move.TACKLE, Move.TRIATTACK, Move.VICEGRIP, Move.VINEWHIP, Move.WATERFALL,
                           Move.WATERGUN, Move.WINGATTACK, ],
    MoveGroupName.SWIFT: [Move.SWIFT],
    MoveGroupName.QUICKATTACK: [Move.QUICKATTACK],
    MoveGroupName.SPLASH: [Move.ROAR, Move.SPLASH, Move.TELEPORT, Move.WHIRLWIND],
    MoveGroupName.HYPERBEAM: [Move.HYPERBEAM],
    MoveGroupName.FLINCH_10: [Move.BONECLUB, Move.HYPERFANG],
    MoveGroupName.FLINCH_30: [Move.BITE, Move.HEADBUTT, Move.LOWKICK, Move.ROLLINGKICK, Move.STOMP],
    MoveGroupName.DIG: [Move.DIG, Move.FLY],
    MoveGroupName.BLIZZARD: [Move.BLIZZARD],
    MoveGroupName.FREEZE_10: [Move.ICEBEAM, Move.ICEPUNCH],
    MoveGroupName.PARALYSIS_10: [Move.THUNDER, Move.THUNDERBOLT, Move.THUNDERPUNCH, Move.THUNDERSHOCK],
    MoveGroupName.PARALYSIS_30: [Move.LICK],
    MoveGroupName.BODYSLAM: [Move.BODYSLAM],
    MoveGroupName.BURN_10: [Move.EMBER, Move.FIREPUNCH, Move.FLAMETHROWER],
    MoveGroupName.BURN_30: [Move.FIREBLAST],
    MoveGroupName.POISON_20: [Move.POISONSTING],
    MoveGroupName.POISON_40: [Move.SLUDGE, Move.SMOG],
    MoveGroupName.HYPNOSIS: [Move.HYPNOSIS, Move.LOVELYKISS, Move.SING, Move.SLEEPPOWDER, Move.SPORE],
    MoveGroupName.TOXIC: [Move.TOXIC],
    MoveGroupName.POISONGAS: [Move.POISONGAS, Move.POISONPOWDER],
    MoveGroupName.GLARE: [Move.GLARE, Move.STUNSPORE],
    MoveGroupName.THUNDERWAVE: [Move.THUNDERWAVE],
    MoveGroupName.CRITICAL: [Move.CRABHAMMER, Move.KARATECHOP, Move.RAZORLEAF, Move.SLASH],
    MoveGroupName.EVASION_UP: [Move.DOUBLETEAM, Move.MINIMIZE],
    MoveGroupName.A_UP: [Move.MEDITATE, Move.SHARPEN],
    MoveGroupName.A_UP2: [Move.SWORDSDANCE],
    MoveGroupName.B_UP: [Move.DEFENSECURL, Move.HARDEN, Move.WITHDRAW],
    MoveGroupName.B_UP2: [Move.ACIDARMOR, Move.BARRIER],
    MoveGroupName.C_UP: [Move.GROWTH],
    MoveGroupName.C_UP2: [Move.AMNESIA],
    MoveGroupName.S_UP2: [Move.AGILITY],
    MoveGroupName.ACCURACY_DOWN: [Move.FLASH, Move.KINESIS, Move.SANDATTACK, Move.SMOKESCREEN],
    MoveGroupName.A_DOWN: [Move.GROWL],
    MoveGroupName.B_DOWN: [Move.LEER, Move.TAILWHIP],
    MoveGroupName.B_DOWN2: [Move.SCREECH],
    MoveGroupName.S_DOWN: [Move.STRINGSHOT],
    MoveGroupName.CONFUSE: [Move.CONFUSERAY, Move.SUPERSONIC],
    MoveGroupName.SIDE_A_DOWN: [Move.AURORABEAM],
    MoveGroupName.SIDE_B_DOWN: [Move.ACID],
    MoveGroupName.SIDE_C_DOWN: [Move.PSYCHIC],
    MoveGroupName.SIDE_S_DOWN: [Move.BUBBLE, Move.BUBBLEBEAM, Move.CONSTRICT],
    MoveGroupName.SIDE_CONFUSE: [Move.CONFUSION, Move.PSYBEAM],
    MoveGroupName.CONST_20: [Move.SONICBOOM],
    MoveGroupName.CONST_40: [Move.DRAGONRAGE],
    MoveGroupName.FISSURE: [Move.FISSURE, Move.GUILLOTINE, Move.HORNDRILL],
    MoveGroupName.EXPLOSION: [Move.EXPLOSION, Move.SELFDESTRUCT],
    MoveGroupName.LEECHSEED: [Move.LEECHSEED],
}  # type: Dict[MoveGroupName, List[Move]]
