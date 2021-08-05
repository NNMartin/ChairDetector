import torch
import torch.nn as nn


def get_model(args: dict, device: torch.device, save=False):
    """
    Returns a PyTorch Neural Net with specifications found in <args> and
    attached to the <device>. If <save> is True, saves the model locally with
    filename <args.save_as>.

    :param args: Dictionary of training specifications detailed in main.py.
    :param device: GPU or CPU to load model onto.
    :param save: Whether to save model or not.
    :return: torch.Module
    """
    model = torch.hub.load(
        'pytorch/vision:v0.9.0', args.model_link, pretrained=True
        )
    model.fc = nn.Linear(2048, args.num_classes)
    if save:
        torch.save(model, args.save_as)
    return model.to(device)
