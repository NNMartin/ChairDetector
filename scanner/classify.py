import torch
from torchvision import transforms
from torch.nn.functional import softmax
from PIL import Image
from urllib.request import urlopen
from torch.nn import Module
from selenium.webdriver.remote.webelement import WebElement


def init_model(model_path: str):
    """
    Loads PyTorch neural net located at <model_path>, and sets the model to
    evaluation mode.

    :param model_path: Global path to PyTorch model.
    :return: Module
    """
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()
    return model


def process_image(image: Image):
    """
    Returns torch.Tensor of <image> after passing it through transforms. The
    transforms are taken from the model webpage:
    https://pytorch.org/hub/pytorch_vision_resnext/

    :param image: Image to be processed into torch.Tensor to be input into
            a neural net.
    :return: torch.Tensor
    """
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
            ),
        ])
    return preprocess(image).unsqueeze(0)


def get_prob(model: Module, image: Image):
    """
    Returns the probability of <image>, calculated by the neural net <model>.
    The category of interest is assumed to be the first index of model output.

    :param model: Neural net used for image classification.
    :param image: Image to be classified
    :return: float
    """
    mod_input = process_image(image)
    output = model(mod_input)
    return softmax(output[0], dim=0)[0].item()


def hm_prob(image: WebElement, image_name: str, model: Module):
    """
    Downloads the image <image> with the global path name <image_name> and
    returns the probability of that image being a particular item, as
    calculated by the neural net <model>.

    :param image: Image to be downloaded and classified.
    :param image_name: Global file path used to name the image and store it
            locally.
    :param model: Neural network used for image classification.
    :return: float
    """
    src = image.get_attribute('src')
    conn = urlopen(src)
    with open(image_name, "wb") as download:
        download.write(conn.read())
    with open(image_name, 'rb') as img:
        mod_input = Image.open(img).convert('RGB')
        prob = get_prob(model, mod_input)
    return prob
