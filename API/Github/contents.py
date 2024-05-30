'''API interface Module for Github Content calls'''
import base64
import json
import requests

from API.Github.github_base_calls import GithubBaseCalls


# File wide variables
ENDPOINT = 'contents'


class Contents():
    '''Class for Github Contents API functions'''

    def GetFileFromRepository(
        owner: str,
        repo_name: str,
        filePath: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to get a file content'''

        if logging:
            print(f'Getting file "{filePath}" with Github "/{ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{ENDPOINT}/{filePath}',
            is_jpl=is_jpl,
            logging=logging)


    def GetDecodedFileContent(
        owner: str,
        repo_name: str,
        filePath: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> str:
        '''Function to decode the file content'''

        response: requests.Response = Contents.GetFileFromRepository(
            owner=owner,
            repo_name=repo_name,
            filePath=filePath,
            is_jpl=is_jpl,
            logging=logging
        )

        if response.status_code == 200:
            json_content = json.loads(response.content)
            decoded_content = base64.b64decode(json_content['content'])
            return f'{decoded_content}'

        return f'File "{filePath}" not found!'
