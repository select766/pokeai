from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.party_db import fs_checkpoint, unpack_obj


def load_trainer(trainer_id_with_battles: str) -> Trainer:
    # trainer_id@battles 形式で指定されたモデルをロード
    elems = trainer_id_with_battles.split("@")
    if len(elems) == 1:
        f = fs_checkpoint.get_last_version(elems[0])
    elif len(elems) == 2:
        f = fs_checkpoint.find_one({"filename": elems[0], "metadata": {"battles": int(elems[1])}})
    else:
        raise ValueError(f"Invalid trainer_id {trainer_id_with_battles}")
    trainer = Trainer.load_state(unpack_obj(f.read()), resume=False)
    return trainer
