import json
import pickle
from pathlib import Path
from typing import Union

ROOT_DIR = Path(__file__).resolve().parents[1]  # type: Path
DATASET_DIR = ROOT_DIR.joinpath('data', 'dataset')  # type:Path


def json_load(path: Union[str, Path]):
    with open(path) as f:
        return json.load(f)


def json_dump(obj, path: Union[str, Path]):
    with open(path, "w") as f:
        json.dump(obj, f)


def pickle_load(path: Union[str, Path]):
    with open(path, 'rb') as f:
        return pickle.load(f)


def pickle_dump(obj, path: Union[str, Path]):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)
