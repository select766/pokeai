import pickle
import yaml


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
