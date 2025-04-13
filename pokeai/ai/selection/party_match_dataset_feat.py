"""
パーティマッチデータセットの特徴量を生成するスクリプト
"""

import argparse
import json

import torch
from pokeai.sim.party_generator import Party
from pokeai.util import json_load, json_dump, DATASET_DIR

FEAT_DIM = 5 # 1vs1の特徴量次元数(ポケモン、技*4)

def get_party_feat(party: Party, mapping: dict) -> list:
    """
    パーティの特徴量を取得する
    :param party:
    :param mapping:
    :return:
    """
    feat = []
    for poke in party:
        feat.append(mapping["poke"][poke["species"]])
        for move in poke["moves"]:
            feat.append(mapping["move"][move])
        # 技が4つない場合、技なしのトークンを追加
        for _ in range(4 - len(poke["moves"])):
            feat.append(mapping["move"]["<move_empty>"])
    assert len(feat) == FEAT_DIM, f"feat: {feat}, len: {len(feat)}"
    return feat

def get_payoff(wincount: list[int]) -> float:
    """
    パーティ1側の利得を取得する
    
    :param wincount: 勝利数のリスト
    :return: 利得 (-1~1)
    """
    total_wins = wincount[0] + wincount[2] * 0.5
    total_games = sum(wincount)
    if total_games == 0:
        return 0.0
    return total_wins / total_games * 2 - 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_feat", help="output path (pytorch tensor)")
    parser.add_argument("input_match", help="input path (jsonl)")
    parser.add_argument("mapping", help="mapping path (json)")
    args = parser.parse_args()

    mapping = json_load(args.mapping)["mapping"]
    payoffs = []
    feats = []
    with open(args.input_match, "r") as f:
        for line in f:
            record = json.loads(line)
            feats.append([get_party_feat(party, mapping) for party in record["parties"]])
            payoffs.append(get_payoff(record["wincounts"]))
    
    # save as pytorch tensor
    feats = torch.tensor(feats, dtype=torch.int32)
    payoffs = torch.tensor(payoffs, dtype=torch.float32)


    torch.save({"feats": feats, "payoffs": payoffs}, args.output_feat)

if __name__ == '__main__':
    main()
