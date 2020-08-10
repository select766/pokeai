import os
import subprocess
import copy
import argparse
import numpy as np
from bson import ObjectId
import optuna
from pokeai.util import yaml_dump
from pokeai.ai.party_db import col_rate

CONFIG_DIR = ""

train_param_tmpl = {
    "tags": ["hyperparam_search"],
    "battles": 100000,
    "party_tags": ["good_200614_2"],
    "trainer": {
        "model_params": {
            "n_layers": 3,
            "n_channels": 16,
            "bn": False,
        },
        "dqn_params": {},
        "feature_params": {},
    }
}

evaluate_base_trainer_id = ObjectId("5ee60e21f420ac034d11d316")
evaluate_party_tag = "good_200614_3"


def make_train_param(epsilon: float, epsilon_decay: float, gamma: float, lr: float):
    trainer_param = copy.deepcopy(train_param_tmpl)
    trainer_param["trainer"]["dqn_params"] = {
        "epsilon": epsilon,
        "epsilon_decay": epsilon_decay,
        "gamma": gamma,
        "lr": lr,
    }
    return trainer_param


def get_mean_by_prefix(rates, prefix):
    f_rates = []
    for player_id, rate in rates.items():
        if player_id.startswith(prefix):
            f_rates.append(rate)
    return np.mean(f_rates)


def get_rate_advantage(rate_id, base_trainer_id, target_trainer_id):
    rates = col_rate.find_one({"_id": rate_id})["rates"]
    base_mean_rate = get_mean_by_prefix(rates, str(base_trainer_id))
    target_mean_rate = get_mean_by_prefix(rates, str(target_trainer_id))
    return float(target_mean_rate - base_mean_rate)  # float: JSON serializableにする


def objective(trial):
    trainer_ids = [ObjectId() for _ in range(10)]  # 10%進むごとに各trainer_idでモデル保存
    trainer_param = make_train_param(epsilon=trial.suggest_uniform("epsilon", 0.1, 0.5),
                                     epsilon_decay=trial.suggest_loguniform("epsilon_decay", 1e-7, 1e-5),
                                     gamma=trial.suggest_uniform("gamma", 0.8, 1.0),
                                     lr=trial.suggest_loguniform("lr", 1e-4, 1e-1))
    trainer_param_file_path = os.path.join(CONFIG_DIR, f"trainer_{trainer_ids[-1]}.yaml")
    yaml_dump(trainer_param, trainer_param_file_path)
    subprocess.check_call(
        ["python", "-m", "pokeai.ai.generic_move_model.rl_train", trainer_param_file_path, "--trainer_id",
         ",".join(map(str, trainer_ids))])
    rate_advantages = []
    for trainer_id in trainer_ids:
        rate_id = ObjectId()
        print(rate_id)
        subprocess.check_call(
            ["python", "-m", "pokeai.ai.generic_move_model.rl_rating_battle",
             f"{evaluate_base_trainer_id},{trainer_id}",
             evaluate_party_tag, "--rate_id", str(rate_id), "--loglevel", "WARNING"])
        rate_advantage = get_rate_advantage(rate_id, evaluate_base_trainer_id, trainer_id)
        print(rate_advantage)
        rate_advantages.append(rate_advantage)
    trial.set_user_attr("trainer_ids", list(map(str, trainer_ids)))  # JSON serializableである必要あり
    trial.set_user_attr("rate_advantages", rate_advantages)
    return -rate_advantages[-1]  # 最後のtrainer_idに対応する値を最小化


def main():
    global CONFIG_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("config_dir")
    parser.add_argument("--study_name", required=True)
    parser.add_argument("--storage", required=True)
    parser.add_argument("--n_trials", type=int, default=100)
    args = parser.parse_args()

    CONFIG_DIR = args.config_dir
    study = optuna.load_study(study_name=args.study_name, storage=args.storage)
    study.optimize(objective, n_trials=args.n_trials)


if __name__ == '__main__':
    main()
