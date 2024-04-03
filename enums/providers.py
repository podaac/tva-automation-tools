from enum import Enum


class Providers(Enum):
    POCUMULUS = 1
    POCLOUD = 2

    @staticmethod
    def from_str(label):
        if label.lower() == "pocloud":
            return Providers.POCLOUD
        elif label.lower() == "pocumulus":
            return Providers.POCUMULUS
        else:
            NotImplemented
