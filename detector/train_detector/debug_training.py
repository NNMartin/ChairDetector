from detector.train_detector.main import ArgsDict
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
import torch
from torchvision import transforms, datasets
from detector.train_detector.create_dataset import get_data


def wrong_predictions(args: dict):
    """
    Returns a list of indices from the dataset located at <args.folder> whose
    predictions are incorrect.

    :param args: Dictionary of training specifications detailed in main.py.
    :return: list
    """
    model = torch.load(args.saved_model, map_location=torch.device('cpu'))
    model.eval()
    image_data = get_data(args.folder, args.dimensions)
    dl = DataLoader(image_data)
    incorrect = []
    for i, (image, label) in enumerate(dl):
        outputs = model(image)
        _, predicted = torch.max(outputs.data, 1, keepdim=True)
        if predicted != label:
            print(i)
            incorrect.append(i)
    return incorrect


def process_data(folder: str, dimensions: int):
    """
    Given the local path to the data <folder> of images, retrieve the images
    and return an ImageFolder dataset using the transforms outlined on the
    model webpage: https://pytorch.org/hub/pytorch_vision_resnext/. However,
    normalization is not included. This is to avoid distorting the images
    when plotted.

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
        [transforms.Resize(256),
        transforms.CenterCrop(dimensions),
        transforms.ToTensor()]
        )
    return datasets.ImageFolder(folder, transform=preprocess)


def plot_prediction(args: dict, index: int):
    """
    Plots image located at <index> in dataset found in <args.folder> and prints
    the true and predicted labels.

    :param args: Dictionary of training specifications detailed in main.py.
    :param index: Index of image data to plot.
    :return: None
    """
    model = torch.load(args.saved_model, map_location=torch.device('cpu'))
    model.eval()
    image_data = get_data(args.folder, args.dimensions)
    image, label = image_data[index]
    output = model(image.unsqueeze(0))
    _, predicted = torch.max(output.data, 1, keepdim=True)
    print("label: ", label)
    print("predicted: ", predicted.item())
    image = process_data(args.folder, args.dimensions)[index][0]
    plt.imshow(image.permute(1, 2, 0))


if __name__ == "__main__":
    args = ArgsDict()
    args_dict = {
        "gpu": False,
        "model_link": "resnext50_32x4d",
        "epochs": 5,
        "folder": "data/",
        "dimensions": 224,
        "batch_size": 8,
        "s": 5,
        "learning_rates": [0.004, 0.1, 0.02, 0.0008, 0.0001],
        "seed": 6802,
        "num_classes": 2,
        "saved_model": "model.pt"
        }
    args.update(args_dict)
    print(len(wrong_predictions(args)))
