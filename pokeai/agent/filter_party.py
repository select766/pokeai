"""
パーティをレーティングによってフィルタリングして出力する。
"""

import os
import argparse
from typing import Dict, List, Tuple, Callable
import numpy as np
from pokeai.agent.util import load_pickle, save_pickle, save_yaml


def filter_party(out_prefix, parties_file, rates_file, count):
    parties = load_pickle(parties_file)["parties"]
    uuid_rates = load_pickle(rates_file)["rates"]
    rate_idxs = []
    for i, party_data in enumerate(parties):
        rate = uuid_rates[party_data["uuid"]]
        rate_idxs.append((rate, i))

    if count < 0:
        count = len(rate_idxs) // 2
    top_rate_idxs = list(sorted(rate_idxs, reverse=True))[:count]
    out_parties = []
    out_uuid_rates = {}
    for _, idx in top_rate_idxs:
        party_data = parties[idx]
        out_parties.append(party_data)
        out_uuid_rates[party_data["uuid"]] = uuid_rates[party_data["uuid"]]

    save_pickle({"parties": out_parties}, out_prefix + ".bin")
    save_pickle({"rates": out_uuid_rates}, out_prefix + "_rate.bin")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst_prefix")
    parser.add_argument("src_prefix")
    parser.add_argument("--count", type=int, default=-1, help="上位いくつのパーティを出力するか")
    args = parser.parse_args()
    filter_party(args.dst_prefix, args.src_prefix + ".bin", args.src_prefix + "_rate.bin", args.count)


if __name__ == '__main__':
    main()
