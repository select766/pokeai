# -*- coding:utf-8 -*-

import random
import copy
from pokeai_simu import Poke, PokeStaticParam, MoveID, PokeType, Dexno, Party

poke_sts = []
available_moves = list(MoveID)
available_moves.remove(MoveID.Empty)

def get_random_poke():
    poke_st = copy.copy(random.choice(poke_sts))
    poke_st.move_ids = random.sample(available_moves, 4)
    return Poke(poke_st)

def get_random_party(size=3):
    pokes = []
    existing_dexnos = []
    while len(pokes) < size:
        poke = get_random_poke()
        # 同じポケモンを複数体含めないための条件
        if poke.static_param.dexno not in existing_dexnos:
            pokes.append(poke)
            existing_dexnos.append(poke.static_param.dexno)
    return Party(pokes)

def _init_poke_list():
    """
    ポケモンのタイプ・能力値リストを作成
    技は与えない
    """

    poke = PokeStaticParam()
    poke.dexno = Dexno.Dugtrio
    poke.type1 = PokeType.Ground
    poke.type2 = PokeType.Empty
    poke.max_hp = 142
    poke.st_a = 132
    poke.st_b = 102
    poke.st_c = 122
    poke.st_s = 172
    poke.base_s = 120
    poke_sts.append(poke)

    poke = PokeStaticParam()
    poke.dexno = Dexno.Alakazam
    poke.type1 = PokeType.Psychc
    poke.type2 = PokeType.Empty
    poke.max_hp = 162
    poke.st_a = 102
    poke.st_b = 97
    poke.st_c = 187
    poke.st_s = 172
    poke.base_s = 120
    poke_sts.append(poke)
    
    poke = PokeStaticParam()
    poke.dexno = Dexno.Gengar
    poke.type1 = PokeType.Ghost
    poke.type2 = PokeType.Poison
    poke.max_hp = 167
    poke.st_a = 117
    poke.st_b = 112
    poke.st_c = 182
    poke.st_s = 162
    poke.base_s = 110
    poke_sts.append(poke)
    
    poke = PokeStaticParam()
    poke.dexno = Dexno.Exeggutor
    poke.type1 = PokeType.Grass
    poke.type2 = PokeType.Psychc
    poke.max_hp = 202
    poke.st_a = 147
    poke.st_b = 137
    poke.st_c = 177
    poke.st_s = 107
    poke.base_s = 55
    poke_sts.append(poke)
    
    poke = PokeStaticParam()
    poke.dexno = Dexno.Starmie
    poke.type1 = PokeType.Water
    poke.type2 = PokeType.Psychc
    poke.max_hp = 167
    poke.st_a = 127
    poke.st_b = 137
    poke.st_c = 152
    poke.st_s = 167
    poke.base_s = 115
    poke_sts.append(poke)

    poke = PokeStaticParam()
    poke.dexno = Dexno.Jynx
    poke.type1 = PokeType.Ice
    poke.type2 = PokeType.Psychc
    poke.max_hp = 172
    poke.st_a = 102
    poke.st_b = 87
    poke.st_c = 147
    poke.st_s = 147
    poke.base_s = 95
    poke_sts.append(poke)
    
    poke = PokeStaticParam()
    poke.dexno = Dexno.Tauros
    poke.type1 = PokeType.Normal
    poke.type2 = PokeType.Empty
    poke.max_hp = 182
    poke.st_a = 152
    poke.st_b = 147
    poke.st_c = 122
    poke.st_s = 162
    poke.base_s = 110
    poke_sts.append(poke)
    
    poke = PokeStaticParam()
    poke.dexno = Dexno.Lapras
    poke.type1 = PokeType.Water
    poke.type2 = PokeType.Ice
    poke.max_hp = 237
    poke.st_a = 137
    poke.st_b = 132
    poke.st_c = 147
    poke.st_s = 112
    poke.base_s = 60
    poke_sts.append(poke)
    
    poke = PokeStaticParam()
    poke.dexno = Dexno.Jolteon
    poke.type1 = PokeType.Electr
    poke.type2 = PokeType.Empty
    poke.max_hp = 172
    poke.st_a = 117
    poke.st_b = 112
    poke.st_c = 162
    poke.st_s = 182
    poke.base_s = 130
    poke_sts.append(poke)

_init_poke_list()
