# JavascriptベースのレーティングバトルのログにBattleStatusを追加する

import argparse
import json
import re
import numpy as np
from pokeai.util import json_load, pickle_load, ROOT_DIR, DATASET_DIR, json_dump
from collections import defaultdict
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.ai.action_policy import ActionPolicy
from pokeai.ai.common import get_possible_actions

players = ["p1", "p2"]


def _extractUpdateForSide(side: str, chunk_data: str):
    # Pokemon-Showdown/sim/battle.ts の移植
    if side == 'omniscient':
        # 全データ取得
        return re.sub('\n\\|split\\|p[1234]\n([^\n]*)\n(?:[^\n]*)', '\n\\1', chunk_data)
    # 各プレイヤーごとの秘密情報を、他のプレイヤー向けには削除する
    # '|split|p1'の次の行は、p1にのみ送る（他のプレイヤーの場合削除）
    if side.startswith('p'):
        chunk_data = re.sub('\n\\|split\\|' + side + '\n([^\n]*)\n(?:[^\n]*)', '\n\\1', chunk_data)
    return re.sub('\n\\|split\\|(?:[^\n]*)\n(?:[^\n]*)\n\n?', '\n', chunk_data)  # 対象でない秘密データ削除


def process_one_battle(orig_log):
    bsps = {k: BattleStreamProcessor() for k in players}
    for k, bsp in bsps.items():
        bsp.set_policy(ActionPolicy())  # 実際にactionを要求するとNotImplementedになる
        bsp.start_battle(k, orig_log["agents"][k]["party"])
    for entry in orig_log["events"]:
        if entry["type"] == "choice":
            player = entry["choice"]["player"]
            pas = get_possible_actions(bsps[player], entry["choice"]["request"])
            entry["choice"]["battle_status"] = json.loads(bsps[player].battle_status.json_dumps())
            entry["choice"]["possible_actions"] = [pa._asdict() for pa in pas]
            slog = entry["choice"].get("searchLog")
            q_func = None
            # 思考経過ログから、q関数相当の値を抽出
            if isinstance(slog, list) and len(slog) > 0:
                slogentry = slog[-1]
                if slogentry["type"] == "MC":
                    q_values = [wr["winrate"] for wr in slogentry["payload"]["winrates"]]
                    action = int(np.argmax(q_values))
                    q_func = {"q_func": q_values, "action": action}
            entry["choice"]["q_func"] = q_func
        elif entry["type"] == "update":
            for k, bsp in bsps.items():
                bsp.process_chunk("update", _extractUpdateForSide(k, "\n".join(entry["update"])))
    return orig_log


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()
    with open(args.src) as f:
        with open(args.dst, "w") as fw:
            for line in f:
                assigned = process_one_battle(json.loads(line))
                fw.write(json.dumps(assigned) + "\n")


if __name__ == '__main__':
    main()
