"""Harmony module"""
# pylint: disable=R0903

from API.harmony import Version
from enums import Environment


class Harmony():
    """Class for Harmony related methods"""

    def GetVersionFromHarmony(serviceName:str, environment:str) -> str:
        """Function to get the version of the git repository active on Harmony"""

        return Version.GetVersionFor(
            jsonVariableName = serviceName,
            environment = Environment.FromStr(environment),
            logging = True)
