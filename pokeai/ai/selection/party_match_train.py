"""
パーティの対戦結果予測モデルを学習する
"""

import argparse
from pathlib import Path
import torch
from pokeai.ai.selection.party_match_model import PartyMatchModel

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("train_feat")
    parser.add_argument("val_feat")
    parser.add_argument("work_dir")
    args = parser.parse_args()

    train_dataset = load_dataset(args.train_feat)
    val_dataset = load_dataset(args.val_feat)

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    # DataLoader
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False)
    # モデルの定義
    model = PartyMatchModel()
    # optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    # loss function
    criterion = torch.nn.MSELoss()
    # 学習
    for epoch in range(10):
        model.train()
        for i, (feats, payoffs) in enumerate(train_loader):
            optimizer.zero_grad()
            outputs = model(feats[:, 0, :], feats[:, 1, :])
            loss = criterion(outputs, payoffs)
            loss.backward()
            optimizer.step()
            if i % 100 == 0:
                print(f"Epoch {epoch}, Batch {i}, Loss: {loss.item()}")
        # バリデーション
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for feats, payoffs in val_loader:
                outputs = model(feats[:, 0, :], feats[:, 1, :])
                loss = criterion(outputs, payoffs)
                val_loss += loss.item()
        print(f"Epoch {epoch}, Validation Loss: {val_loss / len(val_loader)}")
        # モデルの保存
        torch.save(model.state_dict(), f"{work_dir}/model_epoch_{epoch}.pth")
    print("Training finished.")
    # モデルの保存
    torch.save(model.state_dict(), f"{work_dir}/model_final.pth")
    print("Model saved.")

if __name__ == '__main__':
    main()
