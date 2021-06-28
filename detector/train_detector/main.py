from train_detector.training import best_cv_training
import torch
from train_detector.cnn_model import get_model
import warnings

class ArgsDict(dict):
    def __init__(self, *args, **kwargs):
        super(ArgsDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    args = ArgsDict()
    args_dict = {
        "gpu": True,
        "model_link": "resnext101_32x8d",
        "epochs": 30,
        "folder": "data/",
        "dimensions": 224,
        "batch_size": 16,
        "num_workers": 4,
        "s": 5,
        "learning_rates": [5e-4, 1e-4, 5e-5, 1e-5, 5e-6],
        "label_weights": None,
        "seed": 6802,
        "num_classes": 2,
        "save_as": "og_model.pt"
        }
    args.update(args_dict)
    #model, acc = best_cv_training(args)
    #print('Best Accuracy:', acc)
    #torch.save(model, args.save_as)
