import numpy as np
import torch
from torchvision import transforms, datasets
from torch.utils.data import Subset, DataLoader

def get_data(folder, dimensions):
    preprocess = transforms.Compose(
        [transforms.Resize(256),
        transforms.CenterCrop(dimensions),
        transforms.ToTensor(),
        transforms.Normalize(
            mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225]
            )]
        )
    return datasets.ImageFolder(folder, transform=preprocess)

def cv_index_partitions(n, s):
    """
    n int: number of observations in dataset
    s int: S-fold validation with s (training, validation) pairs.
    returns list((list(int), list(int))): list of (training, validation) indices
        tuples. Where training and validation are lists of randomized indices
        that partition the indices of the original dataset [0, n-1].
    """
    indices = np.arange(n)
    np.random.shuffle(indices)
    val_size = n // s
    for i in range(s):
        training = np.concatenate(
            (indices[0:i*val_size], indices[(i+1)*val_size:])
            )
        validation = indices[i*val_size:(i+1)*val_size]
        yield training, validation

def get_dataloaders(folder, dimensions, batch_size, s, num_workers):
    image_data = get_data(folder, dimensions)
    for train_inds, val_inds in cv_index_partitions(len(image_data), s):
        train_dataloader = DataLoader(
            Subset(image_data, train_inds),
            batch_size = batch_size,
            shuffle = True,
            num_workers = num_workers
            )
        val_dataloader = DataLoader(
            Subset(image_data, val_inds),
            batch_size = batch_size,
            num_workers = num_workers
            )
        yield train_dataloader, val_dataloader
