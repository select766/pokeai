import json
import random
from typing import Optional
from pokeai.ai.observation_converter_raw import ObservationConverterRaw
from pokeai.sim.sim import SimObservation
from pokeai.sim.train_env import TrainEnv, TrainSideStaticEnv, TrainSideStaticEnvBattleConfiguration
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


def random_action(obs: SimObservation) -> Optional[str]:
    reqevent = obs.battle_events[-1]
    if reqevent.action_type in ["turn_start", "force_switch"]:
        pas = get_possible_actions(reqevent.request)
        c = random.choice(pas)
        return c.simulator_key
    else:
        # 行動選択が不要な状況(相手の技/交代選択待ち)
        return None

def test_train_env_step_random_moves():
    def party_pair_generator():
        while True:
            yield get_parties()
    random.seed(1) # 乱数を固定しても、シミュレータ側がランダムな挙動をする
    env = TrainEnv(n_envs=2,party_pair_generator=party_pair_generator(),observation_converter_factory=ObservationConverterRaw)

    obss = env.reset()
    new_battles = 0
    for turn in range(210):
        # 例外を起こさず無限ループもしなければOK
        actions = []
        for i in range(len(obss)):
            actions.append(random_action(obss[i]))
        obss, rewards, dones, infos = env.step(actions)
        for done in dones:
            if done:
                new_battles += 1
    # 最大100ターン(強制交代があっても観測200回)でバトルが終わるので、2バトル並列、4つ観測があれば新しいバトルが4回以上始まるはず
    assert new_battles >= 4

def test_train_side_static_env_step_random_moves():
    def battle_configuration_generator():
        while True:
            yield TrainSideStaticEnvBattleConfiguration(party_pair=get_parties(), static_observation_converter=ObservationConverterRaw(), static_policy=random_action)
    random.seed(1) # 乱数を固定しても、シミュレータ側がランダムな挙動をする
    env = TrainSideStaticEnv(n_envs=2,battle_configuration_generator=battle_configuration_generator(),observation_converter_factory=ObservationConverterRaw)

    obss = env.reset()
    new_battles = 0
    for turn in range(210):
        # 例外を起こさず無限ループもしなければOK
        actions = []
        assert len(obss) == 2
        for i in range(len(obss)):
            actions.append(random_action(obss[i]))
        obss, rewards, dones, infos = env.step(actions)
        for done in dones:
            if done:
                new_battles += 1
    # 最大100ターン(強制交代があっても観測200回)でバトルが終わるので、2バトル並列、2つ観測があれば新しいバトルが4回以上始まるはず
    assert new_battles >= 2
