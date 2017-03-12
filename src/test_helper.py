# -*- coding:utf-8 -*-

from pokeai_simu import *


def get_sample_parties():
    pokes = []

    poke = PokeStaticParam()
    poke.dexno = Dexno.Dugtrio
    poke.move_ids = [MoveID.Blizzard, MoveID.BodySlam,
                     MoveID.ConfuseRay, MoveID.Dig]
    poke.type1 = PokeType.Ground
    poke.type2 = PokeType.Empty
    poke.max_hp = 142
    poke.st_a = 132
    poke.st_b = 102
    poke.st_c = 122
    poke.st_s = 172
    poke.base_s = 120
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Alakazam
    poke.move_ids = [MoveID.DoubleKick, MoveID.DoubleTeam,
                     MoveID.HyperBeam, MoveID.LovelyKiss]
    poke.type1 = PokeType.Psychc
    poke.type2 = PokeType.Empty
    poke.max_hp = 162
    poke.st_a = 102
    poke.st_b = 97
    poke.st_c = 187
    poke.st_s = 172
    poke.base_s = 120
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Gengar
    poke.move_ids = [MoveID.MegaDrain, MoveID.NightShade,
                     MoveID.Psychic, MoveID.Reflect]
    poke.type1 = PokeType.Poison
    poke.type2 = PokeType.Ghost
    poke.max_hp = 167
    poke.st_a = 117
    poke.st_b = 112
    poke.st_c = 182
    poke.st_s = 162
    poke.base_s = 110
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Exeggutor
    poke.move_ids = [MoveID.RockSlide, MoveID.Slash,
                     MoveID.Splash, MoveID.Strength]
    poke.type1 = PokeType.Grass
    poke.type2 = PokeType.Psychc
    poke.max_hp = 202
    poke.st_a = 147
    poke.st_b = 137
    poke.st_c = 177
    poke.st_s = 107
    poke.base_s = 55
    pokes.append(Poke(poke))

    parties = [Party(pokes[0:2]), Party(pokes[2:4])]
    return parties


def get_sample_field(parties=None):
    if parties is None:
        parties = get_sample_parties()
    f = Field(parties)
    f.rng = BattleRngRandom(seed=1)
    f.logger = FieldLoggerPrint()

    return f


action_m0 = FieldActionBegin.move(0)
