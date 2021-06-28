from train_detector.main import ArgsDict
import matplotlib.pyplot as plt
from torch.utils.data import Subset, DataLoader
import torch
from torchvision import transforms, datasets
from train_detector.create_dataset import get_data

def wrong_predictions(args):
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

def process_data(folder, dimensions):
    preprocess = transforms.Compose(
        [transforms.Resize(256),
        transforms.CenterCrop(dimensions),
        transforms.ToTensor()]
        )
    return datasets.ImageFolder(folder, transform=preprocess)

def plot_prediction(args, index):
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
