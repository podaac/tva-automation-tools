'''API interface Module for Github Actions calls'''
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = 'actions'


class Actions():
    '''Class for Github Actions API functions'''

    def GetWorkflowRuns(
        owner: str,
        repo_name: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to get the workflow runs'''

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{ENDPOINT}/runs',
            is_jpl=is_jpl,
            logging=logging)
