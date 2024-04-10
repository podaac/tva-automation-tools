"""API interface Module for Git basic calls"""
import requests

import config


# File wide variables
conf = config.Config

class GitBaseCalls():
    """Class for Git basic API functions"""

    def GetForRepo(endpoint:str, isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function for basic get call to a GIT API endpoint related to repository"""
 
        if logging:
            print(f'Getting data from Git "/{endpoint}" endpoint...')

        url_end = f'/repos/{owner}/{repoName}/{endpoint}'
        return GitBaseCalls.Get(
            endpoint = url_end,
            isJpl = isJpl,
            logging = logging)


    def Get(endpoint:str, isJpl:False, logging:bool=True) -> requests.Response:
        """Function for basic get call to a GIT API endpoint"""
 
        url = ''
        custom_headers = {}
        custom_headers["Accept"] = "application/json"
        if isJpl:
            url = conf.Github_JPL_base
            custom_headers['Authorization'] = f'Bearer {conf.GitToken_JPL}'
        else:
            url = conf.Github_base
            custom_headers['Authorization'] = f'Bearer {conf.GitToken}'

        url = url + endpoint
        response = requests.get(
            url = url,
            headers = custom_headers)

        if (response.status_code != 200) and logging:
            print(f'Response: {response.status_code}')
            print(f'Response text:\r\n{response.text}\r\n')
            print(f'Request url:\r\n{response.request.url}\r\n')

        return response
