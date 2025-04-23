"""
パーティの対戦結果予測モデルを評価する
"""

import argparse
from pathlib import Path
import torch
import optuna
from pokeai.ai.selection.party_match_model import PartyMatchModel
from pokeai.util import pickle_dump
from pokeai.ai.selection.do_loop_baseline import PartyEvaluator
# 依存関係が不自然なのでリファクタリングすべき

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
    parser.add_argument("test_feat")
    parser.add_argument("output", help="prediction output path (pickle)")
    parser.add_argument("--feat_map", required=True, help="mapping path (json)")
    parser.add_argument("--model", required=True, help="model path (pytorch)")
    args = parser.parse_args()

    evaluator = PartyEvaluator(args.feat_map, args.model)
    test_dataset = load_dataset(args.test_feat)

    # DataLoader
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=256, shuffle=False)
    model = evaluator.model
    model.eval()
    val_loss = 0
    criterion = torch.nn.MSELoss()
    expected = []
    actual = []
    with torch.no_grad():
        for feats, payoffs in test_loader:
            outputs = model(feats[:, 0, :], feats[:, 1, :])
            loss = criterion(outputs, payoffs)
            val_loss += loss.item()
            expected.extend(payoffs.tolist())
            actual.extend(outputs.tolist())
    mean_val_loss = val_loss / len(test_loader)
    print(f"Validation Loss: {mean_val_loss}")
    # 予測結果の保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pickle_dump({"expected": expected, "actual": actual}, output_path)

if __name__ == '__main__':
    main()
