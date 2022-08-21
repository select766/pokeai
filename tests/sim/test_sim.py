import json
import random
from pokeai.sim.sim import Sim
from pokeai.ai.common import get_possible_actions

def get_parties():
    party1 = json.loads("""[
      {
        "name": "snorlax",
        "species": "snorlax",
        "moves": [
          "doubleedge",
          "fissure",
          "curse",
          "rest"
        ],
        "ability": "No Ability",
        "evs": {
          "hp": 255,
          "atk": 255,
          "def": 255,
          "spa": 255,
          "spd": 255,
          "spe": 255
        },
        "ivs": {
          "hp": 30,
          "atk": 30,
          "def": 30,
          "spa": 30,
          "spd": 30,
          "spe": 30
        },
        "item": "leftovers",
        "level": 55,
        "shiny": false,
        "gender": "M",
        "nature": ""
      },
      {
        "name": "marowak",
        "species": "marowak",
        "moves": [
          "earthquake",
          "rockslide",
          "fireblast",
          "icywind"
        ],
        "ability": "No Ability",
        "evs": {
          "hp": 255,
          "atk": 255,
          "def": 255,
          "spa": 255,
          "spd": 255,
          "spe": 255
        },
        "ivs": {
          "hp": 30,
          "atk": 30,
          "def": 30,
          "spa": 30,
          "spd": 30,
          "spe": 30
        },
        "item": "thickclub",
        "level": 50,
        "shiny": false,
        "gender": "M",
        "nature": ""
      },
      {
        "name": "zapdos",
        "species": "zapdos",
        "moves": [
          "thunderbolt",
          "hiddenpowerice",
          "thunderwave",
          "rest"
        ],
        "ability": "No Ability",
        "evs": {
          "hp": 255,
          "atk": 255,
          "def": 255,
          "spa": 255,
          "spd": 255,
          "spe": 255
        },
        "ivs": {
          "hp": 30,
          "atk": 30,
          "def": 30,
          "spa": 30,
          "spd": 30,
          "spe": 30
        },
        "item": "miracleberry",
        "level": 50,
        "shiny": false,
        "gender": "N",
        "nature": ""
      }
    ]""")
    party2 = json.loads("""[
      {
        "name": "tauros",
        "species": "tauros",
        "moves": [
          "horndrill",
          "doubleedge",
          "earthquake",
          "substitute"
        ],
        "ability": "No Ability",
        "evs": {
          "hp": 255,
          "atk": 255,
          "def": 255,
          "spa": 255,
          "spd": 255,
          "spe": 255
        },
        "ivs": {
          "hp": 30,
          "atk": 30,
          "def": 30,
          "spa": 30,
          "spd": 30,
          "spe": 30
        },
        "item": "miracleberry",
        "level": 55,
        "shiny": false,
        "gender": "M",
        "nature": ""
      },
      {
        "name": "cloyster",
        "species": "cloyster",
        "moves": [
          "icebeam",
          "surf",
          "icywind",
          "explosion"
        ],
        "ability": "No Ability",
        "evs": {
          "hp": 255,
          "atk": 255,
          "def": 255,
          "spa": 255,
          "spd": 255,
          "spe": 255
        },
        "ivs": {
          "hp": 30,
          "atk": 30,
          "def": 30,
          "spa": 30,
          "spd": 30,
          "spe": 30
        },
        "item": "goldberry",
        "level": 50,
        "shiny": false,
        "gender": "M",
        "nature": ""
      },
      {
        "name": "exeggutor",
        "species": "exeggutor",
        "moves": [
          "psychic",
          "leechseed",
          "sleeppowder",
          "explosion"
        ],
        "ability": "No Ability",
        "evs": {
          "hp": 255,
          "atk": 255,
          "def": 255,
          "spa": 255,
          "spd": 255,
          "spe": 255
        },
        "ivs": {
          "hp": 30,
          "atk": 30,
          "def": 30,
          "spa": 30,
          "spd": 30,
          "spe": 30
        },
        "item": "berryjuice",
        "level": 50,
        "shiny": false,
        "gender": "M",
        "nature": ""
      }
    ]
""")
    return [party1, party2]

def test_sim_step_random_moves():
    random.seed(1) # 乱数を固定しても、シミュレータ側がランダムな挙動をする
    for i in range(10):
        sim = Sim()
        obss = sim.start(get_parties())
        # 例外を起こさず無限ループもしなければOK
        while True:
            actions = []
            for i in [0, 1]:
                reqevent = obss[i].battle_events[-1]
                if reqevent.action_type in ["turn_start", "force_switch"]:
                    pas = get_possible_actions(reqevent.request)
                    c = random.choice(pas)
                    actions.append(c.simulator_key)
                else:
                    # 行動選択が不要な状況(相手の技/交代選択待ち)
                    actions.append(None)
            obss = sim.step(actions)
            if obss[0].is_end:
                break
