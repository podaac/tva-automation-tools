'''Github API interface module'''

import base64
import json
import requests

from API.github.github_base_calls import GithubBaseCalls


# Constants
BASE_ENDPOINT = 'contents'


class Contents():
    '''Github Contents API interface class'''

    def GetFileFromRepository(
        owner: str,
        repo_name: str,
        file_path: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to get a file content'''

        if logging:
            print(f'Getting file "{file_path}" with Github "/{BASE_ENDPOINT}" endpoint...')

        return GithubBaseCalls.Get(
            endpoint=f'/repos/{owner}/{repo_name}/{BASE_ENDPOINT}/{file_path}',
            is_jpl=is_jpl,
            logging=logging)


    def GetDecodedFileContent(
        owner: str,
        repo_name: str,
        file_path: str,
        is_jpl: bool = False,
        logging: bool = True
    ) -> str:
        '''Function to decode the file content'''

        response: requests.Response = Contents.GetFileFromRepository(
            owner=owner,
            repo_name=repo_name,
            file_path=file_path,
            is_jpl=is_jpl,
            logging=logging
        )

        if response.status_code == 200:
            json_content = json.loads(response.content)
            decoded_content = base64.b64decode(json_content['content'])
            return f'{decoded_content}'

        return f'File "{file_path}" not found!'
