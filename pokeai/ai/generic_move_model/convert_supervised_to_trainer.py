"""
教師あり学習で学習したモデルをTrainerの形式に変換して、rl_rating_battle.pyで評価可能にする
既存の具体的なモデルの変換用で汎用性なし
"""

import torch
from bson import ObjectId
from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.party_db import col_trainer, pack_obj


def main():
    trainer = Trainer({"n_layers": 3, "n_channels": 16, "bn": False}, {}, {})
    trainer.model.load_state_dict(torch.load(r"experiment\gmm\train\200216_12\model.pt")["model_state_dict"])

    trainer_id = ObjectId()
    col_trainer.insert_one({
        "_id": trainer_id,
        "trainer_packed": pack_obj(trainer.save_state()),
        "train_params": {},
        "tags": ["supervised"],
    })
    print("trainer id", trainer_id)


if __name__ == '__main__':
    main()
