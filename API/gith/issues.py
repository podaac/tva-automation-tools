'''Github API interface module'''
# pylint: disable=R0801, R0903
# R0801 => Calling a method shouldn't count as duplicate code
# R0903 => Need only 1 public method

import requests

from API.gith.github_base_calls import GithubBaseCalls


# Constants
BASE_ENDPOINT = 'issues'


class Issues():
    '''Github Issues API interface class'''

    def GetIssues(
        owner: str,
        repo_name: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the issues endpoint'''

        if logging:
            print(f'Getting data from Github "/{BASE_ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{BASE_ENDPOINT}',
            is_jpl=is_jpl,
            logging=logging)
