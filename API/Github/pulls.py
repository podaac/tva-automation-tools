'''API interface Module for Github Pull Requests calls'''
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = 'pulls'


class PullRequests():
    '''Class for Github Pull Requests API functions'''

    def GetPullRequests(
        owner: str,
        repo_name: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the pull requests endpoint'''

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{ENDPOINT}',
            is_jpl=is_jpl,
            logging=logging)
