import torch
from torchvision import transforms
from torch.nn.functional import softmax
from PIL import Image
from urllib.request import urlopen


def init_model(model_path):
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()
    return model


def process_image(image):
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
    mod_input = process_image(image)
    output = model(mod_input)
    return softmax(output[0], dim=0)[0].item()


def hm_prob(image, image_name, model):
    src = image.get_attribute('src')
    conn = urlopen(src)
    with open(image_name, "wb") as download:
        download.write(conn.read())
    with open(image_name, 'rb') as img:
        mod_input = Image.open(img).convert('RGB')
        prob = get_prob(model, mod_input)
    return prob
