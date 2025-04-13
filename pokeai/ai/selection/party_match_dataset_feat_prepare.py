import argparse
from pokeai.util import json_load, json_dump, DATASET_DIR

def create_mapping(regulation):
    """
    regulationを指定し、ポケモン・技からその埋め込み番号へのマッピングを作成する
    """
    pokemons = json_load(DATASET_DIR.joinpath('regulations', regulation, 'pokemons.json'))
    moves = json_load(DATASET_DIR.joinpath('regulations', regulation, 'moves.json'))
    idx = 0
    mapping_poke = {}
    mapping_move = {}
    inverse_mapping = {}
    for species in ["<poke_empty>"] + pokemons:
        mapping_poke[species] = idx
        inverse_mapping[idx] = f"poke/{species}"
        idx += 1
    # 念のため、技なしのトークンを用意
    for move in ["<move_empty>"] + moves:
        mapping_move[move] = idx
        inverse_mapping[idx] = f"move/{move}"
        idx += 1
    return {"mapping": {"poke": mapping_poke, "move": mapping_move}, "inverse": inverse_mapping}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="output path (json)")
    parser.add_argument("-r", default="default", help="regulation")
    args = parser.parse_args()

    mapping = create_mapping(args.r)
    json_dump(mapping, args.output)

if __name__ == '__main__':
    main()
