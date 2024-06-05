'''Github API interface module'''
# pylint: disable=R0903
# R0801 => Logging out api response shouldn't count as duplicate code

import requests

import config.config


# Constants
Conf = config.Config


class GithubBaseCalls():
    '''Github base API interface class'''

    def GetForRepo(
        endpoint: str,
        owner: str,
        repo_name: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function for basic get call to a Github API endpoint related to repository'''

        if logging:
            print(f'Getting data from Github "/{endpoint}" endpoint...')

        url_end = f'/repos/{owner}/{repo_name}/{endpoint}'
        return GithubBaseCalls.Get(
            endpoint=url_end,
            is_jpl=is_jpl,
            logging=logging)


    def Get(
        endpoint: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function for basic get call to a Github API endpoint'''

        url = ''
        custom_headers = {}
        custom_headers['Accept'] = 'application/json'
        if is_jpl:
            url = Conf.Github_JPL_base
            custom_headers['Authorization'] = f'Bearer {Conf.Github_Token_JPL}'
        else:
            url = Conf.Github_base
            custom_headers['Authorization'] = f'Bearer {Conf.Github_Token}'

        url = url + endpoint
        response = requests.get(
            url=url,
            headers=custom_headers)

        if (response.status_code != 200) and logging:
            print(f'Response: {response.status_code}')
            print(f'Response text:\r\n{response.text}\r\n')
            print(f'Request url:\r\n{response.request.url}\r\n')

        return response
