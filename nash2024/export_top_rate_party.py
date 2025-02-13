import argparse
from pokeai.ai.party_db import col_party, col_rate
from bson import ObjectId
from pokeai.util import json_dump


def load_parties(player_ids):
    party_ids = {player_id.split('+')[1] for player_id in player_ids}
    return {party_id:col_party.find_one({"_id":ObjectId(party_id)})["party"] for party_id in party_ids}


def export_top_parties(rate_id, path):
    rates = col_rate.find_one({"_id": ObjectId(rate_id)})["rates"]
    rate_tuples = [(rate, player_id) for player_id, rate in rates.items()]
    rate_tuples.sort()
    player_ids = []
    for rate, player_id in rate_tuples[-1:-101:-1]:
        player_ids.append(player_id)
    json_dump({"player_ids": player_ids}, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rate_id")
    parser.add_argument("out", help="output json file path of rate ids")
    args = parser.parse_args()
    export_top_parties(args.rate_id, args.out)


if __name__ == "__main__":
    main()
