"""
パーティ特徴抽出器
現在2技関係=["P", "M", "I", "PP", "MM", "PM", "PI", "MI"]が実装されている。
"""
from typing import List

import numpy as np

from pokeai.sim.party_generator import Party
from pokeai.util import DATASET_DIR
from pokeai.util import json_load

# ポケモンのid ["bulbasaur", ...]
_all_pokemons = json_load(DATASET_DIR.joinpath('all_pokemons.json'))  # type: List[str]
_pokemon2idx = {name: i for i, name in enumerate(_all_pokemons)}
# 技のid ["absorb", ...]
_all_moves = json_load(DATASET_DIR.joinpath('all_moves.json'))  # type: List[str]
_move2idx = {name: i for i, name in enumerate(_all_moves)}
# 道具のid ["", "berryjuice", ...]
# 道具なし状態に対応する""が含まれている。
_all_items = json_load(DATASET_DIR.joinpath('all_items.json'))  # type: List[str]
_item2idx = {name: i for i, name in enumerate(_all_items)}


class PartyFeatureExtractor:
    names: List[str]  # 特徴量名
    total_dims: int  # 次元数
    N_POKES = len(_all_pokemons)
    N_MOVES = len(_all_moves)
    N_ITEMS = len(_all_items)
    DIM_P = N_POKES
    DIM_M = N_MOVES
    DIM_I = N_ITEMS
    DIM_PP = N_POKES * (N_POKES - 1) // 2
    DIM_MM = N_MOVES * (N_MOVES - 1) // 2
    DIM_PM = N_POKES * N_MOVES
    DIM_PI = N_POKES * N_ITEMS
    DIM_MI = N_MOVES * N_ITEMS
    ALL_NAMES = ["P", "M", "I", "PP", "MM", "PM", "PI", "MI"]
    DIMS = {
        "P": DIM_P,
        "M": DIM_M,
        "I": DIM_I,
        "PP": DIM_PP,
        "MM": DIM_MM,
        "PM": DIM_PM,
        "PI": DIM_PI,
        "MI": DIM_MI,
    }

    def __init__(self, names: List[str]):
        self.names = names
        self.total_dims = sum(PartyFeatureExtractor.DIMS[name] for name in names)
        self._get_features = {
            "P": self._get_feature_p,
            "M": self._get_feature_m,
            "I": self._get_feature_i,
            "PP": self._get_feature_pp,
            "MM": self._get_feature_mm,
            "PM": self._get_feature_pm,
            "PI": self._get_feature_pi,
            "MI": self._get_feature_mi,
        }

    def get_dimensions(self):
        """
        各次元の意味をリストにして返す。
        :return: 各次元の内容を表すタプルのリスト
        """

        dims = []
        getters = {
            "P": self._get_dimensions_p,
            "M": self._get_dimensions_m,
            "I": self._get_dimensions_i,
            "PP": self._get_dimensions_pp,
            "MM": self._get_dimensions_mm,
            "PM": self._get_dimensions_pm,
            "PI": self._get_dimensions_pi,
            "MI": self._get_dimensions_mi,
        }
        for name in self.names:
            dims.extend(getters[name]())
        return dims

    def _get_dimensions_p(self):
        dims = []
        # P
        for d in _all_pokemons:
            dims.append(("P", d))
        return dims

    def _get_dimensions_m(self):
        dims = []
        # M
        for m in _all_moves:
            dims.append(("M", m))
        return dims

    def _get_dimensions_i(self):
        dims = []
        # I
        for i in _all_items:
            dims.append(("I", i))
        return dims

    def _get_dimensions_pp(self):
        dims = []
        # PP
        for di in range(len(_all_pokemons)):
            for dj in range(di + 1, len(_all_pokemons)):
                dims.append(("PP", _all_pokemons[di], _all_pokemons[dj]))
        return dims

    def _get_dimensions_mm(self):
        dims = []
        # MM (1匹のポケモンが覚えている2技の組)
        for mi in range(len(_all_moves)):
            for mj in range(mi + 1, len(_all_moves)):
                dims.append(("MM", _all_moves[mi], _all_moves[mj]))
        return dims

    def _get_dimensions_pm(self):
        dims = []
        # PM
        for d in _all_pokemons:
            for m in _all_moves:
                dims.append(("PM", d, m))
        return dims

    def _get_dimensions_pi(self):
        dims = []
        # PI
        for d in _all_pokemons:
            for it in _all_items:
                dims.append(("PI", d, it))
        return dims

    def _get_dimensions_mi(self):
        dims = []
        # MI
        for m in _all_moves:
            for it in _all_items:
                dims.append(("MI", m, it))
        return dims

    def get_feature(self, party: Party) -> np.ndarray:
        """
        パーティの特徴量を抽出する。
        :param party: パーティ
        :return: 特徴量ベクトル
        """
        feat = np.zeros((self.total_dims,), dtype=np.float32)
        offset = 0
        for name in self.names:
            dim = PartyFeatureExtractor.DIMS[name]
            subfeat = feat[offset:offset + dim]  # view
            self._get_features[name](party, subfeat)
            offset += dim
        return feat

    def _get_feature_p(self, party: Party, feat: np.ndarray):
        for poke in party:
            # P
            feat[_pokemon2idx[poke['species']]] = 1

    def _get_feature_m(self, party: Party, feat: np.ndarray):
        for poke in party:
            # M
            for m in poke['moves']:
                feat[_move2idx[m]] = 1

    def _get_feature_i(self, party: Party, feat: np.ndarray):
        for poke in party:
            # I
            feat[_item2idx[poke['item']]] = 1

    def _get_feature_pp(self, party: Party, feat: np.ndarray):
        # PP
        for pi in range(len(party)):
            for pj in range(pi + 1, len(party)):
                dn1 = _pokemon2idx[party[pi]['species']]
                dn2 = _pokemon2idx[party[pj]['species']]
                if dn1 > dn2:
                    dn1, dn2 = dn2, dn1
                idx = dn1 * (2 * PartyFeatureExtractor.N_POKES - dn1 - 3) // 2 + dn2 - 1
                feat[idx] = 1

    def _get_feature_mm(self, party: Party, feat: np.ndarray):
        for poke in party:
            moves = poke['moves']
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
                    m1 = _move2idx[moves[mi]]  # 0-origin
                    m2 = _move2idx[moves[mj]]
                    if m1 > m2:
                        m1, m2 = m2, m1
                    idx = m1 * (2 * PartyFeatureExtractor.N_MOVES - m1 - 3) // 2 + m2 - 1
                    feat[idx] = 1

    def _get_feature_pm(self, party: Party, feat: np.ndarray):
        for poke in party:
            # PM
            # p1m1, p1m2, ..., p2m1, p2m2の順
            for m in poke['moves']:
                idx = _pokemon2idx[poke['species']] * PartyFeatureExtractor.N_MOVES + _move2idx[m]
                feat[idx] = 1

    def _get_feature_pi(self, party: Party, feat: np.ndarray):
        for poke in party:
            # PI
            idx = _pokemon2idx[poke['species']] * PartyFeatureExtractor.N_ITEMS + _item2idx[poke['item']]
            feat[idx] = 1

    def _get_feature_mi(self, party: Party, feat: np.ndarray):
        for poke in party:
            # MI
            for m in poke['moves']:
                idx = _move2idx[m] * PartyFeatureExtractor.N_ITEMS + _item2idx[poke['item']]
                feat[idx] = 1
