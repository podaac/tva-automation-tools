'''API interface Module for Harmony Versions calls'''
import requests
import json

from enums import Environment
import config


# File wide variables
conf = config.Config
endpoint = '/versions'


class Version():
    '''Class for Harmony Versions API functions'''

    def GetVersion(
        environment: Environment,
        logging: bool = True
    ) -> requests.Response:
        '''Function to call the versions endpoint'''

        if logging:
            print('Getting data from Harmony "/versions" endpoint...')

        url = ''
        if environment == Environment.OPS:
            url = conf.Harmony_base_OPS + endpoint
        elif environment == Environment.UAT:
            url = conf.Harmony_base_UAT + endpoint

        response = requests.get(
            url=url)

        if (response.status_code != 200) and logging:
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
