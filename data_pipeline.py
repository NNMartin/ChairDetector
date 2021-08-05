from scanner import classify
import os
from PIL import Image
from typing import List


def sort_raw_data(old_dir: str, new_dir: str, model_path: str, delta=0.2):
    """
    Moves image data from old directory to a new directory and sorts the data
    based off of the image classification of a neural network model.

    :param old_dir: Path to directory containing raw data.
    :param new_dir: Path to directory containing sorted data.
    :param model_path: Path to neural network.
    :param delta: Float in (0,0.5). Any model output probability that falls
            within (0.5 - delta, 0.5 + delta) is deemed to uncertain to
            classify when sorting raw data.
    :return: None
    """
    data = {"HM": [], "NHM": [], "uncertain": []}
    model = classify.init_model(model_path)
    for image in os.listdir(old_dir):
        image_path = old_dir + "/" + image
        with open(image_path, 'rb') as img:
            mod_input = Image.open(img).convert('RGB')
            prob = classify.get_prob(model, mod_input)
            if prob >= 0.5 + delta:
                data["hm"].append(image)
            elif prob <= 0.5 - delta:
                data["nhm"].append(image)
            else:
                data["uncertain"].append(image)
    for key, val in data.items():
        move_files(val, old_dir, new_dir + "/" + key)


def move_files(files: List[str], old_dir: str, new_dir: str):
    """
    Move <files> from one directory to another.

    :param files: List of file names.
    :param old_dir: Path to directory that files are currently located in.
    :param new_dir: Path to directory that files are to be moved to.
    :return: None
    """
    for file in files:
        os.rename(old_dir + "/" + file, new_dir + "/" + file)


def move_data(old_dir: str, new_dir: str):
    """
    Moves files from old directory to a new directory.

    :param old_dir: Path to directory that files are currently located in.
    :param new_dir: Path to directory that files are to be moved to.
    :return: None
    """
    data = {"HM": [], "NHM": [], "uncertain": []}
    for (dir_path, dir_names, filenames) in os.walk(old_dir):
        for dir_name in dir_names:
            if dir_name == "uncertain":
                continue
            for image in os.listdir(dir_path):
                data[dir_name].append(dir_path + "/" + image)
            move_files(data[dir_name], dir_path, new_dir + "/" + "dir_name")
