"""API interface Module for Github Packages calls"""
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = "packages"

class Packages():
    """Class for Github Packages API functions"""

    def GetPackages(isJpl:False, owner:str, logging:bool=True) -> requests.Response:
        """Function to call the packages endpoint"""

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint = f'/orgs/{owner}/{ENDPOINT}?package_type=container',
            isJpl = isJpl,
            logging = logging)


    def GetPackagesDetails(isJpl:False, owner:str, packageName:str, packageType:str='container', logging:bool=True) -> requests.Response:
        """Function to call the packages endpoint"""

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint = f'/orgs/{owner}/{ENDPOINT}/{packageType}/{packageName}/versions',
            isJpl = isJpl,
            logging = logging)
