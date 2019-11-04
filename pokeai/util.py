import json


def json_load(path: str):
    with open(path) as f:
        return json.load(f)


def json_dump(obj, path: str):
    with open(path, "w") as f:
        json.dump(obj, f)
