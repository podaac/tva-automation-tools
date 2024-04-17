"""API interface Module for Github Pull Requests calls"""
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = "pulls"

class PullRequests():
    """Class for Github Pull Requests API functions"""

    def GetPullRequests(isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function to call the pull requests endpoint"""

        if logging:
            print(f'Getting data from Github "/{ENDPOINT}" endpoint...')
        
        return GithubBaseCalls.Get(
            endpoint = f'/repos/{owner}/{repoName}/{ENDPOINT}',
            isJpl = isJpl,
            logging = logging)

