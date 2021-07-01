import torch
from torchvision import transforms

def init_model(model_path):
    model = torch.load(model_path, map_location=torch.device('cpu'))
    model.eval()
    return model
def process_image(model, image):
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
    input = process_image(image)
    output = model(input)
    return torch.nn.functional.softmax(output[0], dim = 0)[0].item()
