'''Enum for Environments'''
from enum import Enum


class Environment(Enum):
    '''Environment Enum'''

    OPS = 1
    UAT = 2

    @staticmethod
    def FromStr(label):
        '''Method to turn string into the Enum'''

        if label.lower() == 'ops':
            return Environment.OPS
        if label.lower() == 'uat':
            return Environment.UAT
        raise NotImplementedError(f'Environment for "{label}" is not implemented!')
