'''Enum for CMR Provider'''
from enum import Enum


class Provider(Enum):
    '''Provider Enum'''

    POCUMULUS = 1
    POCLOUD = 2

    @staticmethod
    def FromStr(label):
        '''Method to turn string into the Enum'''

        if label.lower() == 'pocloud':
            return Provider.POCLOUD
        if label.lower() == 'pocumulus':
            return Provider.POCUMULUS
        raise NotImplementedError(f'Provider for "{label}" is not implemented!')
