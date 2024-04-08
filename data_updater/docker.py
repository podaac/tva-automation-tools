"""Docker module"""
# pylint: disable=R0903


class Docker():
    """Class for Docker related methods"""

    def GetDockerPackageLink(environment:str) -> str:
        """Function to get the package link of the git repository published to Docker"""
        raise NotImplementedError()