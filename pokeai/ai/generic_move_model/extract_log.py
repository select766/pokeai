"""
rating_battle.py のログを読み込み、各局面での行動をデータセットとして抽出する。
"""

import argparse
import os

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc
from bson import ObjectId
import numpy as np
from pokeai.util import json_load, pickle_load, ROOT_DIR, DATASET_DIR, pickle_base64_loads, pickle_dump
import json
import re
from collections import defaultdict


def extract_json(line):
    return line[line.find("{"):line.rfind("}") + 1]


def process(log, outdir):
    # 'DEBUG:__main__:match start: 5e3e1f9d3bef84bdd2dff9f7, 5e3da5625491fc3299f850bc\n'
    re_match_start = re.compile("DEBUG:__main__:match start: ([0-9a-f]{24}), ([0-9a-f]{24})")
    # DEBUG:__main__:match end: winner: 0
    re_winner = re.compile("DEBUG:__main__:match end: winner: (0|1|-1)")  # -1は引き分け
    status_log_prefix = "DEBUG:pokeai.sim.battle_stream_processor:choice_turn_start:"
    current_agent_ids = None
    current_battle_logs = None
    agent_logs = defaultdict(list)  # エージェントをキーとしてログを蓄積
    with open(log) as f:
        for line in f:
            m = re_match_start.match(line)
            if m:
                current_agent_ids = m.group(1), m.group(2)
                current_battle_logs = [[], []]  # p1, p2
                continue
            if line.startswith(status_log_prefix):
                status = json.loads(extract_json(line))  # {battle_status:..., request: ..., choice: "move X"}
                battle_status = pickle_base64_loads(status["battle_status"])  # type: BattleStatus
                side = {"p1": 0, "p2": 1}[battle_status.side_friend]
                if status["request"]["active"][0].get('trapped'):
                    # 複数ターン技などで行動選択ができない状態なので、行動選択学習データに入れない
                    continue
                choice_idx = int(status["choice"][5]) - 1  # "move 2" => 1
                current_battle_logs[side].append({
                    "agent_id": current_agent_ids[side],
                    "battle_status": battle_status,
                    "request": status["request"],
                    "choice_idx": choice_idx,
                    "result": 0  # 自分の側が勝ち=1,負け=-1,引き分け=0
                })
            m = re_winner.match(line)
            if m:
                winner = int(m.group(1))
                for side in [0, 1]:
                    side_all_log = agent_logs[current_agent_ids[side]]
                    result_value = 0 if winner == -1 else (1 if winner == side else -1)
                    for bl in current_battle_logs[side]:
                        bl["result"] = result_value
                        side_all_log.append(bl)
                current_agent_ids = None
                current_battle_logs = None
    for agent_id, agent_log in agent_logs.items():
        pickle_dump(agent_log, os.path.join(outdir, f"{agent_id}.bin"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("outdir")
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    process(args.log, args.outdir)


if __name__ == '__main__':
    main()
