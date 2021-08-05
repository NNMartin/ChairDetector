import numpy as np
from torchvision import transforms, datasets
from torch.utils.data import Subset, DataLoader


def get_data(folder: str, dimensions: int):
    """
    Given the local path to the data <folder> of images, retrieve the images
    and return an ImageFolder dataset using the transforms outlined on the
    model webpage: https://pytorch.org/hub/pytorch_vision_resnext/

    :param folder: Local path to data. Assuming the data has two categories,
            the data should be stored as follows:

            data
                category A
                category B

            where category A and B are folders with parent folder data, and
            category A only contains images of objects classified as A, and
            likewise category B only contains images of objects classified as
            B.
    :param dimensions: Dimensions to crop the height/width of images to.
    :return: datasets.ImageFolder
    """
    preprocess = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(dimensions),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                )
            ]
        )
    return datasets.ImageFolder(folder, transform=preprocess)


def cv_index_partitions(n: int, s: int):
    """
    Returns generator of <s> (training, validation) indices tuples. Where
    training and validation are lists of randomized indices that partition the
    indices of the original dataset [0, <n>-1].

    :param n: Number of observations in dataset.
    :param s: S-fold validation with s (training, validation) pairs.
    :return: generator of (list[int], list[int])
    """
    indices = np.arange(n)
    np.random.shuffle(indices)
    val_size = n // s  # size of validation set
    for i in range(s):
        training = np.concatenate(
            (indices[0:i*val_size], indices[(i+1)*val_size:])
            )
        validation = indices[i*val_size:(i+1)*val_size]
        yield training, validation


def get_dataloaders(folder: str, dimensions: int, batch_size: int, s: int,
                    num_workers: int):
    """
    Retrieves image data from <folder>, processes them using
    torchvision.transforms and returns generator of <s> (train, validation)
    DataLoader tuples.

    :param folder: Local path to data. Assuming the data has two categories,
            the data should be stored as follows:

            data
                category A
                category B

            where category A and B are folders with parent folder data, and
            category A only contains images of objects classified as A, and
            likewise category B only contains images of objects classified as
            B.
    :param dimensions: Dimensions to crop the height/width of images to.
    :param batch_size: The DataLoader batch size.
    :param s: S-fold validation with s (training, validation) pairs.
    :param num_workers: The number of workers when training.
    :return: generator of (DataLoader, DataLoader)
    """
    image_data = get_data(folder, dimensions)
    for train_inds, val_inds in cv_index_partitions(len(image_data), s):
        train_dataloader = DataLoader(
            Subset(image_data, train_inds),
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers
            )
        val_dataloader = DataLoader(
            Subset(image_data, val_inds),
            batch_size=batch_size,
            num_workers=num_workers
            )
        yield train_dataloader, val_dataloader
