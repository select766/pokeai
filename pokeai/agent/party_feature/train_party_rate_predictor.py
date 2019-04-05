"""
パーティ評価関数の学習
"""

import argparse
import pickle
import os
import numpy as np
from bson import ObjectId
from sklearn.model_selection import KFold

from pokeai.agent.party_feature.party_feature_extractor import PartyFeatureExtractor
from pokeai.agent.party_feature.party_rate_predictor import PartyRatePredictor
from pokeai.sim import context
from pokeai.agent import party_db
from ..util import save_pickle, load_yaml, save_yaml


def get_rate_parties(rate_id):
    """
    レーティングと対応するパーティをロードする
    :param rate_id:
    :return: レートリスト, パーティリスト
    """
    rates = []
    parties = []
    for record in party_db.col_rate.aggregate([{"$match": {"_id": rate_id}},
                                               {"$unwind": "$rates"},
                                               {"$project": {"rate": "$rates.rate", "agent_id": "$rates.agent_id"}},
                                               {"$lookup": {"from": "Agent", "localField": "agent_id",
                                                            "foreignField": "_id", "as": "agent"}},
                                               {"$unwind": "$agent"},
                                               {"$project": {"rate": 1, "party_id": "$agent.party_id"}},
                                               {"$lookup": {"from": "Party", "localField": "party_id",
                                                            "foreignField": "_id", "as": "party"}},
                                               {"$unwind": "$party"}
                                               ]):
        #  { "_id" : ObjectId("5c6182bc52338e024b4ef580"), "rate" : 1727.2075623827332, "party_id" : ObjectId("5c6165f452338e9c588ee3b8"), "party" : { "_id" : ObjectId("5c6165f452338e9c588ee3b8"), "party_template" : BinData(0,"...") } }
        rates.append(record["rate"])
        parties.append(pickle.loads(record["party"]["party_template"]))
    return rates, parties


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="回帰器パラメータファイル(yaml)")
    parser.add_argument("rate_id", help="学習データとするレート")
    parser.add_argument("dst_dir", help="回帰器保存ディレクトリ")
    parser.add_argument("--limit", type=int, help="サンプル数を制限する(サンプル数と精度の関係評価用)")
    parser.add_argument("--crossval", type=int, default=0, help="N fold cross validationを行う")
    args = parser.parse_args()
    context.init()
    rates, parties = get_rate_parties(ObjectId(args.rate_id))
    predictor = PartyRatePredictor(load_yaml(args.config))
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
        save_yaml({"mean_scores": mean_scores}, os.path.join(args.dst_dir, "cv_score.yaml"))
    else:
        # 全データで学習
        predictor.fit(parties, rates)
    save_pickle(predictor, os.path.join(args.dst_dir, "party_rate_predictor.bin"))


if __name__ == '__main__':
    main()
