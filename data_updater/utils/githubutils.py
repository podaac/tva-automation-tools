'''Github utility module'''
# pylint: disable=E1101
# E1101 => dynamic method usage

import json
from API.github import Packages


class GitHubUtils():
    '''Class for Github related utility methods'''

    def ExtractRepoData(repo_link: str) -> tuple:
        '''Function to extract information from repository link'''

        github_base = 'https://github.com'
        github_jpl_base = 'https://github.jpl.nasa.gov'
        is_jpl = None
        edited_link = ''
        if repo_link.startswith(github_jpl_base):
            is_jpl = True
            edited_link = repo_link.removeprefix(f'{github_jpl_base}/')
        elif repo_link.startswith(github_base):
            is_jpl = False
            edited_link = repo_link.removeprefix(f'{github_base}/')
        else:
            raise NotImplementedError(f'"{repo_link}" not an Github address!')

        values = edited_link.split('/')
        print(f'is_jpl: {is_jpl}')
        print(f'owner: {values[0]}')
        print(f'repo_name: {values[1]}\r\n')
        return (is_jpl, values[0], values[1])


    def GetPackageDetails(is_jpl: bool, owner: str, repo_link: str) -> tuple:
        '''Function to extract name and type information of package of the repository'''

        response = Packages.GetPackages(is_jpl=is_jpl, owner=owner)
        json_data_list = json.loads(response.text)
        package_name = 'Package Not Found!'
        package_type = ''
        for package in json_data_list:
            if 'repository' not in package:
                continue
            if package['repository']['html_url'] == repo_link:
                package_name = package['name']
                package_type = package['package_type']
                print(f'\r\npackage_name: {package_name}')
                print(f'package_type: {package_type}\r\n')
                break
        return (package_name, package_type)
