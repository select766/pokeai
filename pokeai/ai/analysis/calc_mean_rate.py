"""
レーティングバトル結果に対し、trainer_idごとのレート平均を計算する
"""

import argparse

import numpy as np
from bson import ObjectId

from pokeai.ai.party_db import col_rate


def get_mean_by_prefix(rates, prefix):
    f_rates = []
    for player_id, rate in rates.items():
        if player_id.startswith(prefix):
            f_rates.append(rate)
    return np.mean(f_rates)


def get_prefixes(rates):
    # trainer_idで"xxx@10000"と"xxx@100000"を比較する場合があるため、"+"まで含めてprefixとする
    return set(key.split("+")[0] + "+" for key in rates.keys())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rate_id")
    args = parser.parse_args()
    rates = col_rate.find_one({"_id": ObjectId(args.rate_id)})["rates"]
    print("|trainer_id|mean_rate_id|")
    print("|---|---|")
    for prefix in get_prefixes(rates):
        print(f"|{prefix}|{get_mean_by_prefix(rates, prefix)}|")


if __name__ == '__main__':
    main()
