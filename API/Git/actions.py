"""API interface Module for Git Actions calls"""
import requests

from API.Git.git_base_calls import GitBaseCalls


# File wide variables
ENDPOINT = "actions"

class Actions():
    """Class for Git Actions API functions"""

    def GetWorkflowRuns(isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function to get the workflow runs"""

        if logging:
            print(f'Getting data from Git "/{ENDPOINT}" endpoint...')

        return GitBaseCalls.Get(
            endpoint = f'/repos/{owner}/{repoName}/{ENDPOINT}/runs',
            isJpl = isJpl,
            logging = logging)
