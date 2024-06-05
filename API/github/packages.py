'''Github API interface module'''

import requests

from API.github.github_base_calls import GithubBaseCalls


# Constants
BASE_ENDPOINT = 'packages'


class Packages():
    '''Github Packages API interface class'''

    def GetPackages(
        owner: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the packages endpoint for the list of packages'''

        if logging:
            print(f'Getting package list from Github "/{BASE_ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/orgs/{owner}/{BASE_ENDPOINT}?package_type=container',
            is_jpl=is_jpl,
            logging=logging)


    def GetPackagesDetails(
        owner: str,
        package_name: str,
        package_type: str = 'container',
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the packages endpoint for details of a package'''

        if logging:
            print(f'Getting package details from Github "/{BASE_ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/orgs/{owner}/{BASE_ENDPOINT}/{package_type}/{package_name}/versions',
            is_jpl=is_jpl,
            logging=logging)
