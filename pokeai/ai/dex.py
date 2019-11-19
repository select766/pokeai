from pokeai.util import DATASET_DIR, json_load


class Dex:
    """
    ポケモン等の基本情報を提供するデータベースクラス
    """

    def __init__(self):
        self._pokedex = json_load(DATASET_DIR.joinpath('pokedex.json'))
        self._poke2id = {v['name']: k for k, v in self._pokedex.items()}

    def get_pokedex_by_name(self, name: str) -> dict:
        """
        ポケモン名からポケモン情報を得る
        :param name: ポケモン名　例：'Nidoran-F'
        :return:
        """
        return self._pokedex[self._poke2id[name]]


"""
pokedex.json:
{
  "bulbasaur": {
    "exists": true,
    "name": "Bulbasaur",
    "num": 1,
    "species": "Bulbasaur",
    "types": [
      "Grass",
      "Poison"
    ],
    "genderRatio": {
      "M": 0.875,
      "F": 0.125
    },
    "baseStats": {
      "hp": 45,
      "atk": 49,
      "def": 49,
      "spa": 65,
      "spd": 65,
      "spe": 45
    },
    "abilities": {
      "0": "Overgrow"
    },
    "heightm": 0.7,
    "weightkg": 6.9,
    "color": "Green",
    "evos": [
      "ivysaur"
    ],
    "eggGroups": [
      "Monster",
      "Grass"
    ],
    "eventPokemon": [
      {
        "generation": 2,
        "level": 5,
        "shiny": 1,
        "moves": [
          "tackle",
          "growl",
          "ancientpower"
        ]
      }
    ],
    "tier": "LC",
    "learnset": {
      "ancientpower": [
        "2S0"
      ],
    },
    "id": "bulbasaur",
    "fullname": "pokemon: bulbasaur",
    "effectType": "Pokemon",
    "gen": 1,
    "isUnreleased": false,
    "shortDesc": "",
    "desc": "",
    "isNonstandard": null,
    "noCopy": false,
    "affectsFainted": false,
    "sourceEffect": "",
    "speciesid": "bulbasaur",
    "baseSpecies": "Bulbasaur",
    "forme": "",
    "formeLetter": "",
    "spriteid": "bulbasaur",
    "prevo": "",
    "doublesTier": "LC",
    "nfe": true,
    "gender": "",
    "unreleasedHidden": false,
    "maleOnlyHidden": false,
    "eventOnly": false
  },
"""

dex = Dex()
