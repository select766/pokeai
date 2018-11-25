"""
パーティ特徴抽出器

現在2技関係="PM"が実装されている。
"""

import numpy as np
from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.party import Party


class PartyFeatureExtractor:
    name: str  # 特徴量名
    N_POKES = len(Dexno)  # TODO: この使い方は保証されてる？
    N_MOVES = len(Move)
    DIM_P = N_POKES
    DIM_M = N_MOVES
    DIM_PP = N_POKES * (N_POKES - 1) // 2
    DIM_MM = N_MOVES * (N_MOVES - 1) // 2
    DIM_PM = N_POKES * N_MOVES
    DIM_TOTAL = DIM_P + DIM_M + DIM_PP + DIM_MM + DIM_PM

    def __init__(self, name: str):
        assert name == "PM"
        self.name = name

    def get_dimensions(self):
        """
        各次元の意味をリストにして返す。
        :return: 各次元の内容を表すタプルのリスト
        """

        dims = []
        dexno_list = list(Dexno)
        move_list = list(Move)
        # 1-d
        # P
        for d in dexno_list:
            dims.append((d,))
        # M
        for m in move_list:
            dims.append((m,))
        # 2-d
        # PP
        for di in range(len(dexno_list)):
            for dj in range(di + 1, len(dexno_list)):
                dims.append((dexno_list[di], dexno_list[dj]))
        # MM (1匹のポケモンが覚えている2技の組)
        for mi in range(len(move_list)):
            for mj in range(mi + 1, len(move_list)):
                dims.append((move_list[mi], move_list[mj]))
        # PM
        for d in dexno_list:
            for m in move_list:
                dims.append((d, m))
        assert len(dims) == PartyFeatureExtractor.DIM_TOTAL
        return dims

    def get_feature(self, party: Party) -> np.ndarray:
        """
        パーティの特徴量を抽出する。
        :param party:
        :return:
        """
        feat = np.zeros((PartyFeatureExtractor.DIM_TOTAL,), dtype=np.float32)
        for poke in party.pokes:
            pokest = poke.poke_static
            dexno = pokest.dexno
            moves = pokest.moves

            offset = 0
            # P
            feat[offset + dexno.value - 1] = 1
            offset += PartyFeatureExtractor.DIM_P
            # M
            for m in moves:
                feat[offset + m.value - 1] = 1
            offset += PartyFeatureExtractor.DIM_M
            # PPはスキップ
            offset += PartyFeatureExtractor.DIM_PP
            # MM
            # m1m2, m1m3, ..., m1m165, m2m3, m2m4, ...の順
            for mi in range(len(moves)):
                for mj in range(mi + 1, len(moves)):
                    # 階段状の数列上での座標からシリアル番号を求める
                    # 上三角行列の形、対角成分なし
                    # . 0 1 2 3
                    # . . 4 5 6
                    # . . . 7 8
                    # . . . . 9
                    # . . . . .
                    # 行=y, 列=x, 行数=Nとしたときのインデックスは
                    # y * (2*N-y-3)//2 + x - 1
                    # y < xの条件
                    m1 = moves[mi].value - 1  # 0-origin
                    m2 = moves[mj].value - 1
                    if m1 > m2:
                        m1, m2 = m2, m1
                    idx = m1 * (2 * PartyFeatureExtractor.N_MOVES - m1 - 3) // 2 + m2 - 1
                    feat[offset + idx] = 1
            offset += PartyFeatureExtractor.DIM_MM
            # PM
            # p1m1, p1m2, ..., p2m1, p2m2の順
            for m in moves:
                idx = (dexno.value - 1) * PartyFeatureExtractor.N_MOVES + m.value - 1
                feat[offset + idx] = 1
            offset += PartyFeatureExtractor.DIM_PM

        # PP
        # p1p2, p1p3, ..., p1p151, p2p3, p2p4, ...の順
        offset = PartyFeatureExtractor.DIM_P + PartyFeatureExtractor.DIM_M
        for pi in range(len(party.pokes)):
            for pj in range(pi + 1, len(party.pokes)):
                dn1 = party.pokes[pi].poke_static.dexno.value - 1
                dn2 = party.pokes[pj].poke_static.dexno.value - 1
                if dn1 > dn2:
                    dn1, dn2 = dn2, dn1
                idx = dn1 * (2 * PartyFeatureExtractor.N_POKES - dn1 - 3) // 2 + dn2 - 1
                feat[offset + idx] = 1

        return feat
