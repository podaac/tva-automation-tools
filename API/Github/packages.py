'''API interface Module for Github Packages calls'''
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = 'packages'


class Packages():
    '''Class for Github Packages API functions'''

    def GetPackages(
        owner: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the packages endpoint for the list of packages'''

        if logging:
            print(f'Getting package list from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/orgs/{owner}/{ENDPOINT}?package_type=container',
            is_jpl=is_jpl,
            logging=logging)


    def GetPackagesDetails(
        owner: str,
        packageName: str,
        packageType: str = 'container',
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the packages endpoint for details of a package'''

        if logging:
            print(f'Getting package details from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/orgs/{owner}/{ENDPOINT}/{packageType}/{packageName}/versions',
            is_jpl=is_jpl,
            logging=logging)
