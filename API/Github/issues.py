"""API interface Module for Git Issues calls"""
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = "issues"

class Issues():
    """Class for Git Issues API functions"""

    def GetIssues(isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function to call the issues endpoint"""

        if logging:
            print(f'Getting data from Git "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint = f'/repos/{owner}/{repoName}/{ENDPOINT}',
            isJpl = isJpl,
            logging = logging)
