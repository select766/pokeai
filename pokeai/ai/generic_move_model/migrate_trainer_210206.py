# 2021-02-06以前に学習したTrainerを新形式=gridfs使用に移行

from pokeai.ai.party_db import col_trainer, fs_checkpoint


def main():
    for trainer_dump in col_trainer.find():
        if "trainer_packed" in trainer_dump:
            print(str(trainer_dump["_id"]))
            fs_checkpoint.put(trainer_dump["trainer_packed"], filename=str(trainer_dump["_id"]))
            del trainer_dump["trainer_packed"]
            col_trainer.replace_one({"_id": trainer_dump["_id"]}, trainer_dump)


if __name__ == '__main__':
    main()
