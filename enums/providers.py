"""Enum for CMR Providers"""
from enum import Enum


class Providers(Enum):
    """Providers Enum"""

    POCUMULUS = 1
    POCLOUD = 2

    @staticmethod
    def FromStr(label):
        """Method to turn string into the Enum"""

        if label.lower() == "pocloud":
            return Providers.POCLOUD
        if label.lower() == "pocumulus":
            return Providers.POCUMULUS
        raise NotImplementedError(f'Provider for "{label}" is not implemented!')
