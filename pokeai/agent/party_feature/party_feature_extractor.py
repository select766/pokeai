"""
パーティ特徴抽出器

現在2技関係=["P", "M", "PP", "MM", "PM"]が実装されている。
"""
from typing import List

import numpy as np
from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.party_template import PartyTemplate


class PartyFeatureExtractor:
    names: List[str]  # 特徴量名
    total_dims: int  # 次元数
    N_POKES = len(Dexno)  # TODO: この使い方は保証されてる？
    N_MOVES = len(Move)
    DIM_P = N_POKES
    DIM_M = N_MOVES
    DIM_PP = N_POKES * (N_POKES - 1) // 2
    DIM_MM = N_MOVES * (N_MOVES - 1) // 2
    DIM_PM = N_POKES * N_MOVES
    ALL_NAMES = ["P", "M", "PP", "MM", "PM"]
    DIMS = {
        "P": DIM_P,
        "M": DIM_M,
        "PP": DIM_PP,
        "MM": DIM_MM,
        "PM": DIM_PM,
    }

    def __init__(self, names: List[str]):
        self.names = names
        self.total_dims = sum(PartyFeatureExtractor.DIMS[name] for name in names)
        self._get_features = {
            "P": self._get_feature_p,
            "M": self._get_feature_m,
            "PP": self._get_feature_pp,
            "MM": self._get_feature_mm,
            "PM": self._get_feature_pm,
        }

    def get_dimensions(self):
        """
        各次元の意味をリストにして返す。
        :return: 各次元の内容を表すタプルのリスト
        """

        dims = []
        getters = {"P": self._get_dimensions_p,
                   "M": self._get_dimensions_m,
                   "PP": self._get_dimensions_pp,
                   "MM": self._get_dimensions_mm,
                   "PM": self._get_dimensions_pm}
        for name in self.names:
            dims.extend(getters[name]())
        return dims

    def _get_dimensions_p(self):
        dims = []
        dexno_list = list(Dexno)
        move_list = list(Move)
        # P
        for d in dexno_list:
            dims.append((d,))
        return dims

    def _get_dimensions_m(self):
        dims = []
        dexno_list = list(Dexno)
        move_list = list(Move)
        # M
        for m in move_list:
            dims.append((m,))
        return dims

    def _get_dimensions_pp(self):
        dims = []
        dexno_list = list(Dexno)
        move_list = list(Move)
        # PP
        for di in range(len(dexno_list)):
            for dj in range(di + 1, len(dexno_list)):
                dims.append((dexno_list[di], dexno_list[dj]))
        return dims

    def _get_dimensions_mm(self):
        dims = []
        dexno_list = list(Dexno)
        move_list = list(Move)
        # MM (1匹のポケモンが覚えている2技の組)
        for mi in range(len(move_list)):
            for mj in range(mi + 1, len(move_list)):
                dims.append((move_list[mi], move_list[mj]))
        return dims

    def _get_dimensions_pm(self):
        dims = []
        dexno_list = list(Dexno)
        move_list = list(Move)
        # PM
        for d in dexno_list:
            for m in move_list:
                dims.append((d, m))
        return dims

    def get_feature(self, party_t: PartyTemplate) -> np.ndarray:
        """
        パーティの特徴量を抽出する。
        :param party_t: パーティ
        :return: 特徴量ベクトル
        """
        feat = np.zeros((self.total_dims,), dtype=np.float32)
        offset = 0
        for name in self.names:
            dim = PartyFeatureExtractor.DIMS[name]
            subfeat = feat[offset:offset + dim]  # view
            self._get_features[name](party_t, subfeat)
            offset += dim
        return feat

    def _get_feature_p(self, party_t: PartyTemplate, feat: np.ndarray):
        for pokest in party_t.poke_sts:
            dexno = pokest.dexno
            moves = pokest.moves

            # P
            feat[dexno.value - 1] = 1

    def _get_feature_m(self, party_t: PartyTemplate, feat: np.ndarray):
        for pokest in party_t.poke_sts:
            dexno = pokest.dexno
            moves = pokest.moves
            # M
            for m in moves:
                feat[m.value - 1] = 1

    def _get_feature_pp(self, party_t: PartyTemplate, feat: np.ndarray):
        # PP
        for pi in range(len(party_t.poke_sts)):
            for pj in range(pi + 1, len(party_t.poke_sts)):
                dn1 = party_t.poke_sts[pi].dexno.value - 1
                dn2 = party_t.poke_sts[pj].dexno.value - 1
                if dn1 > dn2:
                    dn1, dn2 = dn2, dn1
                idx = dn1 * (2 * PartyFeatureExtractor.N_POKES - dn1 - 3) // 2 + dn2 - 1
                feat[idx] = 1

    def _get_feature_mm(self, party_t: PartyTemplate, feat: np.ndarray):
        for pokest in party_t.poke_sts:
            dexno = pokest.dexno
            moves = pokest.moves
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
                    feat[idx] = 1

    def _get_feature_pm(self, party_t: PartyTemplate, feat: np.ndarray):
        for pokest in party_t.poke_sts:
            dexno = pokest.dexno
            moves = pokest.moves
            # PM
            # p1m1, p1m2, ..., p2m1, p2m2の順
            for m in moves:
                idx = (dexno.value - 1) * PartyFeatureExtractor.N_MOVES + m.value - 1
                feat[idx] = 1
