import pickle
import yaml
import secrets
import random
import numpy as np


def load_pickle(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle(obj: object, path: str):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f)


def save_yaml(obj: object, path: str):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, allow_unicode=True, default_flow_style=False)


def reset_random(seed=None):
    """
    乱数(random, np.random)を再初期化する。
    seed is Noneのとき、OSの乱数生成器によりプロセスごとに異なる初期化がなされる。
    multiprocessingでforkを用いるlinuxでプロセスごとに違う乱数を生成するために利用できる。
    :param seed:
    :return:
    """
    if seed is None:
        seed = secrets.randbelow(2 ** 31)
    random.seed(seed)
    np.random.seed(seed)


def load_party_rate(parties_file, rates_file):
    parties = load_pickle(parties_file)["parties"]
    uuid_rates = load_pickle(rates_file)["rates"]
    party_bodies = []
    rates = []
    for party_data in parties:
        party_bodies.append(party_data["party"])
        rates.append(uuid_rates[party_data["uuid"]])
    return party_bodies, np.array(rates, dtype=np.float)

def randint_len(seq: list) -> int:
    top = len(seq)
    if top <= 0:
        raise ValueError("Sequence length <= 0")
    if top == 1:
        return 0
    # np.random.randint(0)はエラーとなる
    return int(np.random.randint(top - 1))
