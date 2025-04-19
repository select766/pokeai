"""
パーティの対戦結果予測モデルを学習する
Optunaでモデルの構造を最適化する
"""

import argparse
from pathlib import Path
import shutil
import torch
import optuna
from optuna.trial import TrialState
from pokeai.ai.selection.party_match_model import PartyMatchModel
from pokeai.util import json_load


def load_dataset(feat_path):
    """
    データセットを読み込む
    :param feat_path: 特徴量のパス
    :return: 特徴量と利得
    """
    data = torch.load(feat_path, weights_only=True)
    feats = data["feats"]
    payoffs = data["payoffs"]
    # to tensordataset
    return torch.utils.data.TensorDataset(feats, payoffs)

def get_n_vocab_from_mapping(mapping):
    """
    マッピングから語彙数を取得する
    :param mapping: マッピング
    :return: 語彙数
    """
    n_vocab = 0
    for d in mapping.values(): # poke, move
        n_vocab = max(n_vocab, max(d.values()) + 1)
    return n_vocab

class Trainer:
    def __init__(self, train_loader, val_loader, n_vocab, work_dir, device):
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.n_vocab = n_vocab
        self.work_dir = work_dir
    
        self.epoch_count = 10

    def objective(self, trial: optuna.Trial) -> float:
        trial_workdir = self.work_dir / f"trial_{trial.number}"
        trial_workdir.mkdir(parents=True, exist_ok=True)
        print(f"Trial {trial.number} starts")
        # モデルの定義
        embed_dim_order = trial.suggest_int("embed_dim", 4, 8)
        embed_dim = 2 ** embed_dim_order
        mlp_layers = trial.suggest_int("mlp_layers", 2, 4)
        mlp_hidden_dim_order = trial.suggest_int("mlp_hidden_dim", 4, 10)
        mlp_hidden_dim = 2 ** mlp_hidden_dim_order
        party_match_model_hyperparams = {
            "n_vocab": self.n_vocab,
            "embed_dim": embed_dim,
            "mlp_layers": mlp_layers,
            "mlp_hidden_dim": mlp_hidden_dim,
        }
        print(f"Trial {trial.number} hyperparams: {party_match_model_hyperparams}")
        model = PartyMatchModel(**party_match_model_hyperparams)
        model.to(self.device)
        # optimizer
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        # loss function
        criterion = torch.nn.MSELoss()
        # 学習
        for epoch in range(self.epoch_count):
            model.train()
            for i, (feats, payoffs) in enumerate(self.train_loader):
                optimizer.zero_grad()
                feats = feats.to(self.device)
                payoffs = payoffs.to(self.device)
                outputs = model(feats[:, 0, :], feats[:, 1, :])
                loss = criterion(outputs, payoffs)
                loss.backward()
                optimizer.step()
                if i % 1000 == 0:
                    print(f"Epoch {epoch}, Batch {i}, Loss: {loss.item()}")
            # バリデーション
            model.eval()
            val_loss = 0
            with torch.no_grad():
                for feats, payoffs in self.val_loader:
                    feats = feats.to(self.device)
                    payoffs = payoffs.to(self.device)
                    outputs = model(feats[:, 0, :], feats[:, 1, :])
                    loss = criterion(outputs, payoffs)
                    val_loss += loss.item()
            mean_val_loss = val_loss / len(self.val_loader)
            print(f"Epoch {epoch}, Validation Loss: {mean_val_loss}")
            # モデルの保存
            torch.save({"PartyMatchModelWeights": model.state_dict(), "PartyMatchModelHyperparams": party_match_model_hyperparams}, trial_workdir / f"model_epoch_{epoch}.pth")

            trial.report(mean_val_loss, epoch)
            if trial.should_prune():
                print(f"Trial {trial.number} pruned")
                raise optuna.TrialPruned()
        # 最終的なモデルの保存
        torch.save({"PartyMatchModelWeights": model.state_dict(), "PartyMatchModelHyperparams": party_match_model_hyperparams}, trial_workdir / "model_final.pth")
        print(f"Trial {trial.number} finished")
        return mean_val_loss

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("train_feat")
    parser.add_argument("val_feat")
    parser.add_argument("work_dir")
    parser.add_argument("--feat_map", required=True, help="mapping path (json)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="device to use")
    parser.add_argument("--n_trials", type=int, default=100, help="number of trials")
    parser.add_argument("--optuna_storage")
    parser.add_argument("--optuna_study_name")
    args = parser.parse_args()

    train_dataset = load_dataset(args.train_feat)
    val_dataset = load_dataset(args.val_feat)
    n_vocab = get_n_vocab_from_mapping(json_load(args.feat_map)["mapping"])

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    # DataLoader
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=256, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=256, shuffle=False)

    trainer = Trainer(train_loader, val_loader, n_vocab, work_dir, args.device)
    study = optuna.create_study(direction="minimize", storage=args.optuna_storage, study_name=args.optuna_study_name)
    study.optimize(trainer.objective, n_trials=args.n_trials)
    print("Best trial:")
    trial = study.best_trial
    print(f"  Trial: {trial.number}")
    print(f"  Value: {trial.value}")
    print(f"  Params: {trial.params}")

    # copy best trial's model_final.pth to work_dir
    best_trial_workdir = work_dir / f"trial_{trial.number}"
    best_trial_model_path = best_trial_workdir / "model_final.pth"
    best_model_path = work_dir / "best_model.pth"
    shutil.copy(best_trial_model_path, best_model_path)


if __name__ == '__main__':
    main()
