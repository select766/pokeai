"""
パーティ評価関数の学習
"""

import argparse
import pickle
import os
from typing import List, Tuple

import numpy as np
from bson import ObjectId
from sklearn.model_selection import KFold

from pokeai.ai.party_db import col_party, col_agent, col_rate
from pokeai.ai.party_feature.party_rate_predictor import PartyRatePredictor
from pokeai.sim.party_generator import Party
from pokeai.util import pickle_dump, yaml_load, yaml_dump


def get_rate_parties(rate_id: ObjectId) -> Tuple[List[float], List[Party]]:
    """
    レーティングと対応するパーティをロードする
    :param rate_id:
    :return: レートリスト, パーティリスト
    """
    rates = []
    parties = []
    for record in col_rate.aggregate([{"$match": {"_id": rate_id}},
                                      {"$project": {"rates": {"$objectToArray": "$rates"}}},
                                      {"$unwind": "$rates"},
                                      {"$project": {"rate": "$rates.v", "agent_id": {"$toObjectId": "$rates.k"}}},
                                      {"$lookup": {"from": "Agent", "localField": "agent_id",
                                                   "foreignField": "_id", "as": "agent"}},
                                      {"$unwind": "$agent"},
                                      {"$project": {"rate": 1, "party_id": "$agent.party_id"}},
                                      {"$lookup": {"from": "Party", "localField": "party_id",
                                                   "foreignField": "_id", "as": "party"}},
                                      {"$unwind": "$party"},
                                      {"$project": {"rate": 1, "party": "$party.party"}}]):
        # {'_id': ObjectId('5dd903df4c09c8835b995852'),
        # 'rate': 1667.9865011411382,
        # 'party': [{'name': 'magcargo', 'species': 'magcargo', 'moves': ['toxic', 'swagger', 'endure', 'rollout'], ...
        rates.append(record["rate"])
        parties.append(record["party"])
    return rates, parties


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="回帰器パラメータファイル(yaml)")
    parser.add_argument("rate_id", help="学習データとするレート")
    parser.add_argument("dst_dir", help="回帰器保存ディレクトリ")
    parser.add_argument("--limit", type=int, help="サンプル数を制限する(サンプル数と精度の関係評価用)")
    parser.add_argument("--crossval", type=int, default=0, help="N fold cross validationを行う")
    args = parser.parse_args()
    rates, parties = get_rate_parties(ObjectId(args.rate_id))
    predictor = PartyRatePredictor(yaml_load(args.config))
    if args.limit:
        rates = rates[:args.limit]
        parties = parties[:args.limit]
    os.makedirs(args.dst_dir, exist_ok=True)
    if args.crossval > 0:
        scores = []
        for train_idxs, test_idxs in KFold(n_splits=args.crossval).split(parties):
            X_train = [parties[i] for i in train_idxs]
            y_train = [rates[i] for i in train_idxs]
            X_test = [parties[i] for i in test_idxs]
            y_test = [rates[i] for i in test_idxs]
            predictor.fit(X_train, y_train)
            scores.append(predictor.score(X_test, y_test))
        mean_scores = float(np.mean(scores))
        print("mean_scores", mean_scores)
        yaml_dump({"mean_scores": mean_scores}, os.path.join(args.dst_dir, "cv_score.yaml"))
    else:
        # 全データで学習
        predictor.fit(parties, rates)
    pickle_dump(predictor, os.path.join(args.dst_dir, "party_rate_predictor.bin"))


if __name__ == '__main__':
    main()
