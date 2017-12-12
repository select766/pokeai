import yaml
import logging


def yaml_load_file(path):
    with open(path) as f:
        obj = yaml.load(f)
    return obj


def yaml_dump_file(obj, path):
    with open(path, "w") as f:
        yaml.dump(obj, f, default_flow_style=False)


def get_logger(name):
    if name == "__main__":
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)
