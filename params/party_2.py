from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from pokeai.ai_v4.party_generation_helper import get_random_party

PARTY_SIZE = 3

"""
フルアタ構成の簡単なパーティ
"""


def my_party():
    pokes = []

    poke = PokeStaticParam()
    poke.dexno = Dexno.Starmie
    poke.move_ids = [MoveID.Splash, MoveID.Thunderbolt,
                     MoveID.Slash, MoveID.BodySlam]
    poke.type1 = PokeType.Water
    poke.type2 = PokeType.Psychc
    poke.max_hp = 167
    poke.st_a = 127
    poke.st_b = 137
    poke.st_c = 152
    poke.st_s = 167
    poke.base_s = 115
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Lapras
    poke.move_ids = [MoveID.Splash, MoveID.RockSlide,
                     MoveID.Psychic, MoveID.NightShade]
    poke.type1 = PokeType.Water
    poke.type2 = PokeType.Ice
    poke.max_hp = 237
    poke.st_a = 137
    poke.st_b = 132
    poke.st_c = 147
    poke.st_s = 112
    poke.base_s = 60
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Dugtrio
    poke.move_ids = [MoveID.Splash, MoveID.DoubleKick,
                     MoveID.Slash, MoveID.NightShade]
    poke.type1 = PokeType.Ground
    poke.type2 = PokeType.Empty
    poke.max_hp = 142
    poke.st_a = 132
    poke.st_b = 102
    poke.st_c = 122
    poke.st_s = 172
    poke.base_s = 120
    pokes.append(Poke(poke))

    assert len(pokes) == PARTY_SIZE
    return Party(pokes)


def generate_parties():
    return [my_party(), my_party()]
    # return [get_random_party(PARTY_SIZE), get_random_party(PARTY_SIZE)]
