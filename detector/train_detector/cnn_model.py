import torch
import torch.nn as nn

def get_model(args, device, save = False):
    model = torch.hub.load(
        'pytorch/vision:v0.9.0', args.model_link, pretrained = True
        )
    model.fc = nn.Linear(2048, args.num_classes)
    if save:
        torch.save(model, args.save_as)
    return model.to(device)
