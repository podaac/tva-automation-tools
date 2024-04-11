"""API interface Module for Github Actions calls"""
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = "actions"

class Actions():
    """Class for Github Actions API functions"""

    def GetWorkflowRuns(isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function to get the workflow runs"""

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint = f'/repos/{owner}/{repoName}/{ENDPOINT}/runs',
            isJpl = isJpl,
            logging = logging)
