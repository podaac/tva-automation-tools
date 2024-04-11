"""API interface Module for Git Pull Requests calls"""
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = "pulls"

class PullRequests():
    """Class for Git Pull Requests API functions"""

    def GetPullRequests(isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function to call the pull requests endpoint"""

        if logging:
            print(f'Getting data from Git "/{ENDPOINT}" endpoint...')
        
        return GithubBaseCalls.Get(
            endpoint = f'/repos/{owner}/{repoName}/{ENDPOINT}',
            isJpl = isJpl,
            logging = logging)

