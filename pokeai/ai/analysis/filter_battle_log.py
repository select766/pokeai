# 1行1バトルのログファイルにおいて必要なバトルだけを抽出したファイルを生成する
import argparse

from bson import ObjectId
import numpy as np
from pokeai.util import json_load, pickle_load, ROOT_DIR, DATASET_DIR, pickle_base64_loads
import json
import re
import gzip

from pokeai.util import compress_open


def make_pred_player_id(player_id):
    def pred(battle):
        for player_info in battle["agents"].values():
            if player_id == player_info["player_id"]:
                return True
        return False

    return pred


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("--player_id", help="指定したplayer idが含まれるバトルを抽出")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.player_id:
        pred = make_pred_player_id(args.player_id)
    else:
        raise ValueError("filter condition is not supplied")
    write_count = 0
    with compress_open(args.src, "rt") as rf:
        with compress_open(args.dst, "wt") as wf:
            for line in rf:
                battle = json.loads(line)
                if pred(battle):
                    wf.write(line)
                    write_count += 1
                    if args.limit is not None and write_count >= args.limit:
                        break


if __name__ == '__main__':
    main()
