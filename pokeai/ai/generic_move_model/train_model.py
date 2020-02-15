import argparse
import os
import numpy as np
import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import Dataset
from torch.utils.tensorboard import SummaryWriter

from pokeai.ai.generic_move_model.mlp_model import MLPModel


def load_data(data_dir, batch_size, shuffle=False):
    d = np.load(os.path.join(data_dir, "feats.npz"))
    dataset = torch.utils.data.TensorDataset(torch.from_numpy(d["input_feats"]),
                                             torch.from_numpy(d["choices"].astype(np.int64)))
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=0)
    return loader


def train_loop(out_dir, train_loader, val_loader, model, optimizer):
    criterion = nn.CrossEntropyLoss()
    trained_samples = 0
    summary_writer = SummaryWriter(os.path.join(out_dir, "log"))
    for epoch in range(100):
        model.train()
        for input_feats, choices in train_loader:
            optimizer.zero_grad()
            pred = model(input_feats)
            loss = criterion(pred, choices)
            loss.backward()
            optimizer.step()
            pred_label = torch.argmax(pred, 1)
            correct_count = torch.sum(torch.eq(choices, pred_label)).item()
            top1_accuracy = correct_count / len(input_feats)
            trained_samples += len(input_feats)
            summary_writer.add_scalar("train/loss", loss.item(), trained_samples)
            summary_writer.add_scalar("train/top1_accuracy", top1_accuracy, trained_samples)
        model.eval()
        running_loss_times = 0
        running_loss = 0.0
        correct_count = 0
        n_val_items = 0
        with torch.no_grad():
            for input_feats, choices in val_loader:
                pred = model(input_feats)
                loss = criterion(pred, choices)
                pred_label = torch.argmax(pred, 1)
                correct_count += torch.sum(torch.eq(choices, pred_label)).item()
                n_val_items += pred_label.shape[0]
                running_loss += loss.item()
                running_loss_times += 1
        avg_loss = running_loss / running_loss_times
        avg_top1_accuracy = correct_count / n_val_items
        summary_writer.add_scalar("val/avg_loss", avg_loss, trained_samples)
        summary_writer.add_scalar("val/avg_top1_accuracy", avg_top1_accuracy, trained_samples)
        torch.save({"model_state_dict": model.state_dict()}, os.path.join(out_dir, "model.pt"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir")
    parser.add_argument("train_dir")
    parser.add_argument("val_dir")
    args = parser.parse_args()
    train_loader = load_data(args.train_dir, 64, True)
    val_loader = load_data(args.val_dir, 64, False)
    model = MLPModel(558, n_layers=2, n_channels=64)
    optimizer = optim.Adam(model.parameters(), lr=1e-2)
    os.makedirs(args.out_dir, exist_ok=True)
    train_loop(args.out_dir, train_loader=train_loader, val_loader=val_loader, model=model, optimizer=optimizer)


if __name__ == '__main__':
    main()
