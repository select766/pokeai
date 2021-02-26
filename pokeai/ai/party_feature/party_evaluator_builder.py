from pokeai.ai.generic_move_model.trainer_loader import load_trainer
from pokeai.ai.party_feature.party_evaluator import PartyEvaluator
from pokeai.ai.party_feature.party_evaluator_quick import PartyEvaluatorQuick


def build_party_evaluator_by_trainer_id(trainer_id_with_battles: str, party_size: int) -> PartyEvaluator:
    trainer = load_trainer(trainer_id_with_battles)
    agent = trainer.get_val_agent()
    return PartyEvaluator(agent, party_size)


def build_party_evaluator_quick_by_trainer_id(trainer_id_with_battles: str, party_size: int,
                                              device: str) -> PartyEvaluatorQuick:
    trainer = load_trainer(trainer_id_with_battles)
    agent = trainer.get_val_agent()
    return PartyEvaluatorQuick(agent, party_size, device)
