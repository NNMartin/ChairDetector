import torch
from torchvision import transforms
from torch.nn.functional import softmax
from PIL import Image
from urllib.request import urlopen


def init_model(model_path):
    """
    Loads PyTorch neural net located at <model_path>, and sets the model to
    evaluation mode.

    model_path - str: Global path to PyTorch model.
    returns torch.Module
    """
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()
    return model


def process_image(image):
    """
    Returns torch.Tensor of <image> after passing it through transforms. The
    transforms are taken from the model webpage:
    https://pytorch.org/hub/pytorch_vision_resnext/

    image - PIL.Image: Image to be processed into torch.Tensor to be input into
            a neural net.
    returns torch.Tensor
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


def get_prob(model, image):
    """
    Returns the probability of <image>, calculated by the neural net <model>.

    model - torch.Module: Neural net used for image classification.
    image - PIL Image: Image to be classified
    returns float
    """
    mod_input = process_image(image)
    output = model(mod_input)
    return softmax(output[0], dim=0)[0].item()


def hm_prob(image, image_name, model):
    """
    Downloads the image <image> with the global path name <image_name> and
    returns the probability of that image being a particular item, as
    calculated by the neural net <model>.

    model - torch.Module: Neural net used for image classification.
    image - selenium.WebElement: Image to be downloaded and classified.
    image_name - str: Global file path used to name the image and store it
            locally.
    returns float
    """
    src = image.get_attribute('src')
    conn = urlopen(src)
    with open(image_name, "wb") as download:
        download.write(conn.read())
    with open(image_name, 'rb') as img:
        mod_input = Image.open(img).convert('RGB')
        prob = get_prob(model, mod_input)
    return prob
