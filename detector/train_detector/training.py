import torch
import torch.nn as nn
from detector.train_detector.create_dataset import get_dataloaders
from detector.train_detector.cnn_model import get_model
from sklearn.metrics import confusion_matrix
import numpy as np
import time
from torch.utils.data import DataLoader
from typing import Tuple


def best_cv_training(args: dict):
    """
    This function runs S-fold cross validation over <args.s> different learning
    rates and returns the trained model that achieves the highest validation
    accuracy.

    :param args: Dictionary of training specifications detailed in main.py.
    :return: torch.Module, float
    """
    assert len(args.learning_rates) == args.s, (
        "learning_rates should be of size s"
        )
    np.random.seed(args.seed)  # set seed
    dataloader_pairs = get_dataloaders(
        args.folder, args.dimensions, args.batch_size, args.s, args.num_workers
        )
    train_losses, val_losses, metrics = [], [], []
    best_metric = -1
    final_model = None
    for i, pair in enumerate(dataloader_pairs):
        mod, train_loss, val_loss, metric = train(args, i, pair)
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        metrics.append(metric)
        if metric > best_metric:
            best_metric = metric
            final_model = mod
        else:
            del mod  # remove from GPU resources
    return final_model, best_metric


def get_con_stats(true_pred: dict):
    """
    Returns confusion matrix statistics: accuracy, sensitivity, specificity.

    :param true_pred: Dictionary of true labels and predicted labels with keys
            "true" and "pred", whose values are lists populated with 0 or 1
            (category labels).
    :return: float, float, float
    """
    con_mat = confusion_matrix(true_pred["true"], true_pred["pred"])
    acc = (con_mat[0][0] + con_mat[1][1]) / con_mat.sum()
    sens = con_mat[0][0]/con_mat[0].sum()
    spec = con_mat[1][1]/con_mat[1].sum()
    return acc, sens, spec


def print_training_update(epoch: int, duration: float, lr_index: int,
                          losses: Tuple[float], true_pred: dict,
                          period=0):
    """
    Prints epoch training metrics.

    :param epoch: Current training epoch.
    :param duration: Time to complete current epoch training.
    :param lr_index: Index of current learning rate in hyperparameter space.
    :param losses: Tuple of training loss and validation loss.
    :param true_pred: Dictionary of true labels and predicted labels with keys
            "true" and "pred", whose values are lists populated with 0 or 1
            (category labels).
    :param period: Epochs corresponding to a multiple of <period>, an int, will
            be printed.
    :return: None
    """
    if period == 0 or epoch % period == 0:
        train_loss, val_loss = losses
        acc, sens, spec = get_con_stats(true_pred)
        balance = 100*sum(true_pred["true"])/len(true_pred["true"])
        if epoch == 0:
            update = ("======================================================\n"
                "Validation Category Balance: {:0.2f}%\n").format(balance)
        else:
            update = ""
        update += (
            "Learning Rate Index: {}\n"
            "Epoch: {}\n"
            "Time Elapsed: {:0.2f} minutes\n"
            "Train Loss: {:0.2f}\n"
            "Validation Loss: {:0.2f}\n"
            "Validation Accuracy: {:0.2f}\n"
            "Validation Sensitivity: {:0.2f}\n"
            "Validation Specificity: {:0.2f}\n"
            ).format(
                lr_index, epoch, duration, train_loss, val_loss, acc, sens, spec
                )
        print(update)
        print(confusion_matrix(true_pred["true"], true_pred["pred"]), "\n")


def training_metric(true_pred: dict, last_percentile=0.9, metric="acc"):
    """
    Returns the calculated metric of interest during training.

    :param true_pred: Dictionary of true labels and predicted labels with keys
            "true" and "pred", whose values are lists populated with 0 or 1
            (category labels).
    :param last_percentile: If <last_percentile> is 0.9 then the last 10% of
            epochs are used to calculate the training metric.
    :param metric: Possible metrics are: "acc" (accuracy), "sens"
            (sensitivity), or "spec" (specificity).
    :return: float
    """
    last_n_percent = int(last_percentile*len(true_pred["true"]))
    last_true_pred = {
        "true": true_pred["true"][last_n_percent:],
        "pred": true_pred["pred"][last_n_percent:]
    }
    acc, sens, spec = get_con_stats(last_true_pred)
    if metric == "acc":
        return acc
    elif metric == "sens":
        return sens
    elif metric == "spec":
        return spec
    else:
        raise ValueError(
            """Desired metric is not available. Please choose from:
            "acc" (accuracy), "sens" (sensitivity), or "spec" (specificity)"""
            )


def train(args: dict, lr_index: int, dataloaders: Tuple[DataLoader]):
    """
    Trains a neural network using the training specifications in <args> which
    are detailed in main.py. The neural net is trained at the learning rate
    index <lr_index> and uses training, validation dataloaders <dataloaders>.

    :param args: Dictionary of training specifications detailed in main.py.
    :param lr_index: Index of current learning rate in hyperparameter space.
    :param dataloaders: Tuple of training, validation DataLoaders.
    :return: torch.Module, float, float, float
    """
    train_dataloader, val_dataloader = dataloaders
    device = torch.device('cuda') if args.gpu else torch.device('cpu')
    model = get_model(args, device)
    if args.label_weights is None:
        label_weights = None
    else:
        label_weights = args.label_weights.to(device)
    loss_criterion = nn.CrossEntropyLoss(weight=label_weights)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.learning_rates[lr_index]
        )
    train_losses = []
    val_losses = []
    stats = {"true": [], "pred": []}
    for epoch in range(args.epochs):
        start = time.time()
        train_loss = train_epoch(
                model, loss_criterion, optimizer, train_dataloader, device
                )
        val_loss, epoch_stats = val_epoch(
            model, loss_criterion, val_dataloader, device
            )
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        stats["true"] += epoch_stats["true"]
        stats["pred"] += epoch_stats["pred"]
        duration = (time.time() - start) / 60  # epoch duration in minutes
        print_training_update(
            epoch, duration, lr_index, (train_loss, val_loss), epoch_stats
            )
    recent_10_percent = int(0.9*args.epochs)
    return (
        model,
        np.mean(train_losses[recent_10_percent:]),
        np.mean(val_losses[recent_10_percent:]),
        training_metric(stats)
        )


def train_epoch(model, loss_criterion: nn.CrossEntropyLoss,
                optimizer: torch.optim.AdamW, train_dataloader: DataLoader,
                device: torch.device):
    """
    Trains a neural network over an epoch.

    :param model: The neural network to be trained.
    :param loss_criterion: Loss function.
    :param optimizer: Training optimizer.
    :param train_dataloader: Training DataLoader.
    :param device: GPU or CPU for training.
    :return: float
    """
    model.train()
    losses = []
    for images, labels in train_dataloader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = loss_criterion(outputs, labels)
        losses.append(loss.data.item())
        loss.backward()
        optimizer.step()
    return np.mean(losses)


def val_epoch(model, loss_criterion: nn.CrossEntropyLoss,
              val_dataloader: DataLoader, device: torch.device):
    """
    Returns validation loss of neural network <model> as well as
    dictionary of true labels and predicted labels.

    :param model: The neural network to be trained.
    :param loss_criterion: Loss function.
    :param val_dataloader: Validation DataLoader.
    :param device: GPU or CPU for validation.
    :return: float, dict
    """
    model.eval()
    losses = []
    stats = {"true": [], "pred": []}
    for images, labels in val_dataloader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = loss_criterion(outputs, labels)
        losses.append(loss.data.item())
        _, predicted = torch.max(outputs.data, 1, keepdim=True)
        for i in range(labels.size(0)):
            stats["true"].append(labels[i].item())
            stats["pred"].append(predicted[i].item())
    return np.mean(losses), stats
