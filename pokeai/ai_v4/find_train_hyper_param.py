"""
様々なハイパーパラメータで学習を行い、安定するパラメータを探す。
複数個起動する場合は、環境変数を"OMP_NUM_THREADS=1"に設定したほうがよい。
"""

import subprocess
import argparse
import copy
import time
import os
import sys
import tempfile
import random
from . import util

logger = util.get_logger(__name__)


def generate_random_configuration():
    config = {}
    config["model/kwargs/n_hidden_layers"] = random.randint(1, 4)
    config["model/kwargs/n_hidden_channels"] = 2 ** random.randint(4, 8)  # 16 to 128
    config["agent/kwargs/gamma"] = 0.999 - random.random() * 0.1
    config["agent/kwargs/target_update_interval"] = int(10.0 ** (random.random() * 2.0 + 2.0))  # 100 to 10000
    config["train/optimizer/kwargs/alpha"] = 10.0 ** (random.random() * -2.0 - 1.0)  # 1e-1 to 1e-3
    return config


def generate_random_run_config(base_run_config):
    """
    パラメータをランダムに設定したrun_configを作成する。
    :param base_run_config:
    :return: configuration, run_config
    """
    run_config = copy.deepcopy(base_run_config)
    config = generate_random_configuration()
    # スラッシュ区切りのデータを入れ子dictに設定
    # {"abc/def/ghi": 5} => run_config["abc"]["def"]["ghi"] = 5
    for key, value in config.items():
        target_dict = run_config
        split_key = key.split("/")
        for k in split_key[:-1]:
            target_dict = target_dict[k]
        target_dict[split_key[-1]] = value
    return config, run_config


def read_log(train_log_path):
    """
    学習ログを読み、stepに対するスコアを取得する。
    chainerrl.experiments.train_agent_with_evaluation にて出力される形式を想定する。
    :param train_log_path:
    :return: {step: {"mean":mean_score}}
    """
    step_scores = {}
    with open(train_log_path, "r") as f:
        first_line = True
        for line in f:
            if first_line:
                # header
                first_line = False
                continue
            items = line.rstrip().split("\t")
            steps = int(items[0])
            mean = float(items[3])
            step_scores[steps] = {"mean": mean}
    return step_scores


def run_train(run_config):
    """
    学習を走らせて結果を回収する。
    :param run_config:
    :return:
    """
    run_id = f"random_run_{time.strftime('%Y%m%d%H%M%S')}_{os.getpid()}"  # 並列実行で衝突しないように
    logger.info(f"Running training {run_id}")
    fd, run_config_path = tempfile.mkstemp(suffix=".yaml")
    logger.info(f"Temp run config file: {run_config_path}")
    os.close(fd)
    util.yaml_dump_file(run_config, run_config_path)
    subprocess.check_call(
        ["python", "-m", "pokeai.ai_v4.train", run_config_path, "params/party_loader.py", "--run_id", run_id])
    os.remove(run_config_path)
    train_result = read_log(os.path.join("run", run_id, "agent", "scores.txt"))
    return train_result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_run_config")
    parser.add_argument("out_dir")
    parser.add_argument("--n_friend_party", type=int, default=10)
    parser.add_argument("--n_different_config", type=int, default=10)
    args = parser.parse_args()

    base_run_config = util.yaml_load_file(args.base_run_config)
    os.makedirs(args.out_dir, exist_ok=True)
    for config_idx in range(args.n_different_config):
        config, run_config = generate_random_run_config(base_run_config)
        train_results = []
        for party_idx in range(args.n_friend_party):
            run_config_iter = copy.deepcopy(run_config)
            run_config_iter["party_generator"]["train"]["friend_party_idx"] = party_idx
            run_config_iter["party_generator"]["eval"]["friend_party_idx"] = party_idx
            train_result = run_train(run_config_iter)
            train_results.append(train_result)
        util.yaml_dump_file({"config": config, "train_results": train_results},
                            os.path.join(args.out_dir, f"{time.strftime('%Y%m%d%H%M%S')}_{os.getpid()}.yaml"))


if __name__ == '__main__':
    main()
