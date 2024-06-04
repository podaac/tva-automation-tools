'''Harmony API interface module'''
# pylint: disable=R0903
# R0801 => Logging out api response shouldn't count as duplicate code

import json
import requests

from enums import Environment
import config.config


# Constants
Conf = config.Config
BASE_ENDPOINT = '/versions'


class Version():
    '''Harmony Versions API interface class'''

    def GetVersion(
        environment: Environment,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the versions endpoint'''

        if logging:
            print('Getting data from Harmony "/versions" endpoint...')

        url = ''
        if environment == Environment.OPS:
            url = Conf.Harmony_base_OPS + BASE_ENDPOINT
        elif environment == Environment.UAT:
            url = Conf.Harmony_base_UAT + BASE_ENDPOINT

        response = requests.get(
            url=url)

        if response.status_code != 200 and logging:
            print(f'Response: {response.status_code}')
            print(f'Response text:\r\n{response.text}\r\n')
            print(f'Request url:\r\n{response.request.url}\r\n')

        return response


    def GetVersionFor(
        json_variable_name: str,
        environment: Environment,
        logging: bool = True
    ) -> str:
        '''Function to extract the version data for the service'''

        if logging:
            print(f'Getting version of "{json_variable_name}" on "{environment.name}"...')

        response = Version.GetVersion(environment, logging)
        version = 'Not found!'
        json_data = json.loads(response.text)
        for service in json_data:
            for image in service['images']:
                if image['image'] == json_variable_name:
                    version = image['tag']
        return version
