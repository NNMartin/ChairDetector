from scanner.chair_sqlite import init_db
from os import mkdir
import torch
from torch import nn


def init():
    init_db()
    mkdir("scanner/data")


if __name__ == "__main__":
    init()
