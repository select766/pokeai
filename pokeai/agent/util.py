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
