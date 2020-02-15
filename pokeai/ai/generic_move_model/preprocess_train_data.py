"""
extract_log.py の結果を前処理し、DNN学習用の行列へ変換する。
"""

import argparse
import os

from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.generic_move_model.choice_to_vec import ChoiceToVec
import numpy as np
from pokeai.util import json_load, pickle_load, ROOT_DIR, DATASET_DIR, pickle_dump
from pokeai.ai.common import get_possible_actions


def extract_feat(record, feature_extractor: FeatureExtractor, choice_to_vec: ChoiceToVec):
    battle_status = record["battle_status"]
    request = record["request"]
    choice_idxs, choice_keys, choice_vec = get_possible_actions(battle_status, request)

    status_feat = feature_extractor.transform(battle_status, choice_vec)  # (feature_extractor.get_dims(),)
    choice_feat = choice_to_vec.transform(battle_status, request)  # (choice_to_vec.get_dims(), 4)
    combined_feat = np.zeros((status_feat.shape[0] + choice_feat.shape[0], choice_feat.shape[1]), dtype=np.float32)
    combined_feat[:status_feat.shape[0], :] = status_feat[:, np.newaxis]
    combined_feat[status_feat.shape[0]:, :] = choice_feat
    return combined_feat


def process(recorddir, agent_id_list, outdir):
    feature_extractor = FeatureExtractor(party_size=1)
    choice_to_vec = ChoiceToVec()
    input_feats = []
    choices = []
    results = []
    sources = []
    with open(agent_id_list) as f:
        for line in f:
            agent_id = line.rstrip()
            records_file = os.path.join(recorddir, f"{agent_id}.bin")
            records = pickle_load(records_file)
            for i, record in enumerate(records):
                input_feats.append(extract_feat(record, feature_extractor, choice_to_vec))
                choices.append(record["choice_idx"])
                results.append(record["result"])
                sources.append({"agent_id": agent_id, "index": i})
    np.savez_compressed(os.path.join(outdir, "feats.npz"), input_feats=np.stack(input_feats),
                        choices=np.array(choices, dtype=np.int32), results=np.array(results, dtype=np.int32))
    pickle_dump({
        "sources": sources,
        "feature_extractor": feature_extractor,
        "choice_to_vec": choice_to_vec
    }, os.path.join(outdir, "sources.bin"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recorddir")
    parser.add_argument("agent_id_list")
    parser.add_argument("outdir")
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    process(args.recorddir, args.agent_id_list, args.outdir)


if __name__ == '__main__':
    main()
