'''Github API interface module'''
# pylint: disable=R0903
# R0903 => Need only 1 public method

import requests

from API.github.github_base_calls import GithubBaseCalls


# Constants
BASE_ENDPOINT = 'actions'


class Actions():
    '''Github Actions API interface class'''

    def GetWorkflowRuns(
        owner: str,
        repo_name: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to get the workflow runs'''

        if logging:
            print(f'Getting data from Github "/{BASE_ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{BASE_ENDPOINT}/runs',
            is_jpl=is_jpl,
            logging=logging)
