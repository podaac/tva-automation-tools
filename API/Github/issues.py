'''API interface Module for Github Issues calls'''
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = 'issues'


class Issues():
    '''Class for Github Issues API functions'''

    def GetIssues(
        owner: str,
        repo_name: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the issues endpoint'''

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{ENDPOINT}',
            is_jpl=is_jpl,
            logging=logging)
