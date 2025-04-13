"""
ランダムなパーティ同士を対戦させた勝敗のデータセットを作成する
"""

import argparse
import json
from tqdm import tqdm
from pokeai.ai.generic_move_model.rl_rating_battle import match_players
from pokeai.ai.random_policy import RandomPolicy
from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.sim.sim import Sim

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="output path (jsonl)")
    parser.add_argument("-n", type=int, default=100, help="パーティの組み合わせの数")
    parser.add_argument("-m", type=int, default=1, help="1つの組み合わせに対して何回対戦を行うか")
    parser.add_argument("-r", default="default", help="regulation")
    args = parser.parse_args()

    policies = [RandomPolicy() for _ in range(2)]
    gen = RandomPartyGenerator(regulation=args.r)
    sim = Sim()

    with open(args.output, "w") as f:
        for i in tqdm(range(args.n)):
            parties = [gen.generate() for _ in range(2)]
            wincounts = [0, 0, 0]
            for _ in range(args.m):
                # 0/1/-1
                winner = match_players(sim, parties, policies)
                # -1（引き分け）ならwincounts[2]がインクリメント
                wincounts[winner] += 1
            f.write(json.dumps({"parties": parties, "wincounts": wincounts}) + "\n")

if __name__ == '__main__':
    main()
