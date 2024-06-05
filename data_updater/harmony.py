'''Harmony module'''
# pylint: disable=R0903
# R0903 => Need only 1 public method

from API.harmony import Version
from enums import Environment


class Harmony():
    '''Class for Harmony related methods'''

    def GetVersionFromHarmony(environment: str, service_name: str) -> str:
        '''Function to get the version of the Github repository active on Harmony'''

        return Version.GetVersionFor(
            json_variable_name=service_name,
            environment=Environment.FromStr(environment),
            logging=True)
