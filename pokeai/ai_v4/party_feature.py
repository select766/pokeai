"""
パーティの特徴量抽出器

山登り法(iteration=0)のデータを受け取り、特徴量を出力する。
"""

import os
import sys
import copy
import tempfile
from typing import List, Iterable, Set
import pickle
import argparse
from abc import ABCMeta, abstractmethod
import random
import numpy as np
from tqdm import tqdm

from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from .agents import RandomAgent
from . import pokeai_env
from . import party_generation_helper
from . import util
from . import random_rating
from . import find_train_hyper_param
from . import hill_climbing
from . import train

logger = util.get_logger(__name__)


def load_parties(hill_climbing_path):
    parties, run_ids, scores = hill_climbing.load_party_from_hill_climbing(hill_climbing_path, get_score=True)
    return parties, scores


def get_feature_names(feature_types: List[str]) -> List[str]:
    names = []
    # P
    if "p" in feature_types:
        for i in range(len(Dexno)):
            names.append(f"p_{Dexno(i).name}")

    # M
    if "m" in feature_types:
        for i in range(len(MoveID)):
            names.append(f"m_{MoveID(i).name}")

    # PP
    if "pp" in feature_types:
        for i in range(len(Dexno)):
            for j in range(i + 1, len(Dexno)):
                names.append(f"pp_{Dexno(i).name}&{Dexno(j).name}")

    # MM
    if "mm" in feature_types:
        for i in range(len(MoveID)):
            for j in range(i + 1, len(MoveID)):
                names.append(f"mm_{MoveID(i).name}&{MoveID(j).name}")

    # PM
    if "pm" in feature_types:
        for i in range(len(Dexno)):
            for j in range(len(MoveID)):
                names.append(f"pm_{Dexno(i).name}&{MoveID(j).name}")
    return names


def get_all_pairs(item_set: Iterable, allow_self_pair=True) -> Set[set]:
    l = list(item_set)
    inner_offset = 0 if allow_self_pair else 1
    pairs = set()
    for i in range(len(l)):
        for j in range(i + inner_offset, len(l)):
            pairs.add(frozenset([l[i], l[j]]))
    return pairs


def extract_feature(party: Party, feature_types: List[str]):
    elements = []
    # P
    if "p" in feature_types:
        p_set = set([poke.static_param.dexno for poke in party.pokes])
        for i in range(len(Dexno)):
            elements.append(int(Dexno(i) in p_set))

    # M
    if "m" in feature_types:
        m_set = set()
        for poke in party.pokes:
            m_set.update(poke.static_param.move_ids)
        for i in range(len(MoveID)):
            elements.append(int(MoveID(i) in m_set))

    # PP
    if "pp" in feature_types:
        pp_set = get_all_pairs([poke.static_param.dexno for poke in party.pokes], allow_self_pair=False)
        for i in range(len(Dexno)):
            for j in range(i + 1, len(Dexno)):
                elements.append(int(frozenset([Dexno(i), Dexno(j)]) in pp_set))

    # MM
    if "mm" in feature_types:
        mm_set = set()
        for poke in party.pokes:
            mm_set.update(get_all_pairs(poke.static_param.move_ids, allow_self_pair=False))
        for i in range(len(MoveID)):
            for j in range(i + 1, len(MoveID)):
                elements.append(int(frozenset([MoveID(i), MoveID(j)]) in mm_set))

    # PM
    if "pm" in feature_types:
        pm_set = set()
        for poke in party.pokes:
            pm_set.update(frozenset([poke.static_param.dexno, move]) for move in poke.static_param.move_ids)
        for i in range(len(Dexno)):
            for j in range(len(MoveID)):
                elements.append(int(frozenset([Dexno(i), MoveID(j)]) in pm_set))

    return np.array(elements, dtype=np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hill_climbing_path")
    parser.add_argument("-f", "--feature", action="append")
    args = parser.parse_args()
    feature_types = args.feature or ["p", "m", "pp", "mm", "pm"]
    parties, scores = load_parties(args.hill_climbing_path)
    feature_names = get_feature_names(feature_types)
    features = np.vstack([extract_feature(party, feature_types) for party in parties])
    with open(util.get_output_filename("party_feature.pickle"), "wb") as f:
        pickle.dump({"parties": parties, "scores": scores, "feature_names": feature_names, "features": features,
                     "feature_types": feature_types}, f)


if __name__ == '__main__':
    main()
