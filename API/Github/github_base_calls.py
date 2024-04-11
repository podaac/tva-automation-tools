"""API interface Module for Github basic calls"""
import requests

import config


# File wide variables
conf = config.Config

class GithubBaseCalls():
    """Class for Github basic API functions"""

    def GetForRepo(endpoint:str, isJpl:False, owner:str, repoName:str, logging:bool=True) -> requests.Response:
        """Function for basic get call to a Github API endpoint related to repository"""
 
        if logging:
            print(f'Getting data from Github "/{endpoint}" endpoint...')

        url_end = f'/repos/{owner}/{repoName}/{endpoint}'
        return GithubBaseCalls.Get(
            endpoint = url_end,
            isJpl = isJpl,
            logging = logging)


    def Get(endpoint:str, isJpl:False, logging:bool=True) -> requests.Response:
        """Function for basic get call to a Github API endpoint"""
 
        url = ''
        custom_headers = {}
        custom_headers["Accept"] = "application/json"
        if isJpl:
            url = conf.Github_JPL_base
            custom_headers['Authorization'] = f'Bearer {conf.Github_Token_JPL}'
        else:
            url = conf.Github_base
            custom_headers['Authorization'] = f'Bearer {conf.Github_Token}'

        url = url + endpoint
        response = requests.get(
            url = url,
            headers = custom_headers)

        if (response.status_code != 200) and logging:
            print(f'Response: {response.status_code}')
            print(f'Response text:\r\n{response.text}\r\n')
            print(f'Request url:\r\n{response.request.url}\r\n')

        return response
