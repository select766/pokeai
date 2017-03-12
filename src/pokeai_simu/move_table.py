# -*- coding:utf-8 -*-

from .poke_type import PokeType
from .move_id import MoveID
from . import move_handlers


class MoveEntry(object):
    def __init__(self, move_id, move_handler, move_poke_type, attack, accuracy, pp):
        self.move_id = move_id
        self.move_handler = move_handler
        self.move_poke_type = move_poke_type
        self.attack = attack
        self.accuracy = accuracy
        self.pp = pp


class MoveTable(object):
    instance = None

    def __init__(self, entries):
        self.entries = entries  # key: MoveID

    @classmethod
    def get(cls, move_id):
        return cls.instance.entries[move_id]


def _construct_move_table():
    es = [
        MoveEntry(MoveID.Blizzard, move_handlers.MoveHandlerAttack,
                  PokeType.Ice, 120, 70, 5),
        MoveEntry(MoveID.Thunderbolt, move_handlers.MoveHandlerAttack,
                  PokeType.Electr, 95, 100, 15),
        MoveEntry(MoveID.Psychic, move_handlers.MoveHandlerAttack,
                  PokeType.Psychc, 90, 100, 10),
        MoveEntry(MoveID.BodySlam, move_handlers.MoveHandlerAttack,
                  PokeType.Normal, 85, 100, 15),
        MoveEntry(MoveID.Recover, move_handlers.MoveHandlerRecover,
                  PokeType.Normal, 0, 0, 20),
        MoveEntry(MoveID.Reflect, move_handlers.MoveHandlerDoubleTeam,
                  PokeType.Psychc, 0, 0, 20),
        MoveEntry(MoveID.ThunderWave, move_handlers.MoveHandlerToxic,
                  PokeType.Electr, 0, 100, 20),
        MoveEntry(MoveID.DoubleTeam, move_handlers.MoveHandlerDoubleTeam,
                  PokeType.Normal, 0, 0, 15),
        MoveEntry(MoveID.Slash, move_handlers.MoveHandlerAttack,
                  PokeType.Normal, 70, 100, 20),
        MoveEntry(MoveID.RockSlide, move_handlers.MoveHandlerAttack,
                  PokeType.Rock, 75, 90, 10),
        MoveEntry(MoveID.HyperBeam, move_handlers.MoveHandlerHyperBeam,
                  PokeType.Normal, 150, 90, 5),
        MoveEntry(MoveID.LovelyKiss, move_handlers.MoveHandlerToxic,
                  PokeType.Normal, 0, 75, 10),
        MoveEntry(MoveID.Toxic, move_handlers.MoveHandlerToxic,
                  PokeType.Poison, 0, 85, 10),
        MoveEntry(MoveID.Dig, move_handlers.MoveHandlerDig,
                  PokeType.Ground, 60, 100, 10),
        MoveEntry(MoveID.DoubleKick, move_handlers.MoveHandlerAttack,
                  PokeType.Fight, 30, 100, 30),
        MoveEntry(MoveID.Strength, move_handlers.MoveHandlerAttack,
                  PokeType.Normal, 80, 100, 15),
        MoveEntry(MoveID.MegaDrain, move_handlers.MoveHandlerAttack,
                  PokeType.Grass, 40, 100, 10),
        MoveEntry(MoveID.ConfuseRay, move_handlers.MoveHandlerToxic,
                  PokeType.Ghost, 0, 100, 10),
        MoveEntry(MoveID.NightShade, move_handlers.MoveHandlerAttack,
                  PokeType.Ghost, 0, 100, 15),
        MoveEntry(MoveID.Splash, move_handlers.MoveHandlerDoubleTeam,
                  PokeType.Normal, 0, 100, 40),
    ]

    entries_dict = {item.move_id: item for item in es}
    MoveTable.instance = MoveTable(entries_dict)


_construct_move_table()
