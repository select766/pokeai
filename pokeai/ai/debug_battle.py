"""
エージェント同士を対戦させる
メッセージを見てデバッグする用
"""

import argparse
import json
from pokeai.ai.common import load_agent_by_id
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_p1")
    parser.add_argument("agent_p2")
    parser.add_argument("-n", type=int, default=1)
    args = parser.parse_args()
    sim = Sim()
    bsps = []
    parties = []
    for agent_id in [args.agent_p1, args.agent_p2]:
        party, policy = load_agent_by_id(agent_id)
        parties.append(party)
        bsp = BattleStreamProcessor()
        bsp.set_policy(policy)
        bsps.append(bsp)
    sim.set_party(parties)
    sim.set_processor(bsps)
    for i in range(args.n):
        result = sim.run()
        logger.info("result: " + json.dumps(result))


if __name__ == '__main__':
    main()
