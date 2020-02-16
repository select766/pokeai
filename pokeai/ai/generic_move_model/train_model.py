import argparse
import os
import numpy as np
import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data import Dataset
from torch.utils.tensorboard import SummaryWriter

from pokeai.ai.generic_move_model.mlp_model import MLPModel
from pokeai.util import yaml_load


def load_data(data_dir, batch_size, shuffle=False):
    d = np.load(os.path.join(data_dir, "feats.npz"))
    dataset = torch.utils.data.TensorDataset(torch.from_numpy(d["input_feats"]),
                                             torch.from_numpy(d["choices"].astype(np.int64)))
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=0)
    return loader


def train_loop(out_dir, train_loader, val_loader, model, optimizer, train_config):
    criterion = nn.CrossEntropyLoss()
    trained_samples = 0
    summary_writer = SummaryWriter(os.path.join(out_dir, "log"))
    for epoch in range(train_config["epoch"]):
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
    summary_writer.flush()  # flushしないと最後のサンプルが欠損している場合がある


def predict(out_dir, val_loader, model):
    loaded_state_dict = torch.load(os.path.join(out_dir, "model.pt"))
    model.load_state_dict(loaded_state_dict["model_state_dict"])
    del loaded_state_dict
    model.eval()
    preds = []
    with torch.no_grad():
        for input_feats, choices in val_loader:
            pred = model(input_feats).numpy()
            preds.append(pred)
    np.savez(os.path.join(out_dir, "pred.npz"), pred=np.concatenate(preds, axis=0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir")
    parser.add_argument("--predict", action="store_true")
    args = parser.parse_args()
    model_config = yaml_load(os.path.join(args.out_dir, "model.yaml"))
    train_config = yaml_load(os.path.join(args.out_dir, "train.yaml"))
    train_loader = load_data(train_config["dataset"]["train"]["dir"], train_config["dataset"]["train"]["batch_size"],
                             True)
    val_loader = load_data(train_config["dataset"]["val"]["dir"], train_config["dataset"]["val"]["batch_size"],
                           False)
    assert model_config["class"] == "MLPModel"
    model = MLPModel(558, **model_config["kwargs"])
    if args.predict:
        predict(out_dir=args.out_dir, val_loader=val_loader, model=model)
        return
    # optimizer = optim.Adam(model.parameters(), lr=1e-2)
    optimizer = getattr(optim, train_config["optimizer"]["class"])(model.parameters(),
                                                                   **train_config["optimizer"]["kwargs"])
    train_loop(args.out_dir, train_loader=train_loader, val_loader=val_loader, model=model, optimizer=optimizer,
               train_config=train_config)


if __name__ == '__main__':
    main()
