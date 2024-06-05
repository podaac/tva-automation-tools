'''Github module'''
# pylint: disable=C0415, W0612
# C0415 => To avoid circular imports
# W0612 => to ignore unused tuple 3rd element

from datetime import datetime, timedelta
import json
import re

from API.github import Actions, Contents, Issues, Packages, PullRequests
from data_updater.utils import GitHubUtils, WebUtils
from enums import Environment


class Github():
    '''Class for Github related methods'''

    def GetGithubOpenPRCount(repo_link: str) -> int:
        '''Function to get the open pull requests count of the github repository'''

        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        response = PullRequests.GetPullRequests(
            is_jpl=is_jpl,
            owner=owner,
            repo_name=repo_name)
        json_data = json.loads(response.text)
        count = 0
        for elem in json_data:
            if elem['state'] == 'open':
                count += 1
        return count


    def GetGithubOpenIssueCount(repo_link: str) -> int:
        '''Function to get the open issues count of the github repository'''

        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        response = Issues.GetIssues(
            is_jpl=is_jpl,
            owner=owner,
            repo_name=repo_name)
        json_data = json.loads(response.text)
        count = 0
        for elem in json_data:
            if elem['state'] == 'open':
                count += 1
        return count


    def GetGithubLastActionStatus(repo_link: str, branches: list[str]) -> str:
        '''Function to get the status of the last action ran on any of the provided branches of the github repository'''

        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        response = Actions.GetWorkflowRuns(
            is_jpl=is_jpl,
            owner=owner,
            repo_name=repo_name)
        json_data = json.loads(response.text)
        most_recent_run = ''
        result = json_data['workflow_runs'][0]['updated_at']
        for elem in json_data['workflow_runs']:
            if elem['head_branch'] in branches and elem['status'] == 'completed' and elem['updated_at'] >= most_recent_run:
                print('\r\nFound a new one!...')
                result = elem['conclusion']
                most_recent_run = elem['updated_at']
                print(f'result: {result}')
                print(f'updated_at: {most_recent_run}')

        return result


    def GetGithubFailedActionCount(repo_link: str, days_to_check: str, branches: list[str]) -> int:
        '''Function to get the count of the failed action ran
            on any of the provided branches of the github repository
            in the past x days'''

        days_to_check = int(days_to_check)
        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        response = Actions.GetWorkflowRuns(
            is_jpl=is_jpl,
            owner=owner,
            repo_name=repo_name)
        json_data = json.loads(response.text)
        time_of_last = datetime.fromisoformat(json_data['workflow_runs'][0]['updated_at'][:-1])
        time_interval = time_of_last - timedelta(days=days_to_check)
        count = 0
        for elem in json_data['workflow_runs']:
            if elem['head_branch'] in branches and elem['status'] == 'completed' and elem['updated_at'] >= time_interval.isoformat() and elem['conclusion'] == 'failure':
                count += 1
        return count


    def GetGithubPackageVersionTag(repo_link: str, environment: str) -> str:
        '''Function to get the package version of the github repository with the tag of environment'''

        env = Environment.FromStr(environment)
        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        (package_name, package_type) = GitHubUtils.GetPackageDetails(is_jpl=is_jpl, owner=owner, repo_link=repo_link)
        if package_type != '':
            response = Packages.GetPackagesDetails(
                is_jpl=is_jpl,
                owner=owner,
                package_name=package_name,
                package_type=package_type)
            json_data = json.loads(response.text)
            for elem in json_data:
                tags = elem['metadata']['container']['tags']
                if env.name.lower() in tags:
                    for tag in tags:
                        if tag in [env.name.lower(), 'latest']:
                            continue
                        return tag
        return package_name


    def GetGithubPackageLinkWithTag(repo_link: str, environment: str) -> str:
        '''Function to get the package link of the github repository with the tag of environment'''

        env = Environment.FromStr(environment)
        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link=repo_link)
        if is_jpl:
            return 'API does not exists!'
        (package_name, package_type) = GitHubUtils.GetPackageDetails(is_jpl=is_jpl, owner=owner, repo_link=repo_link)
        if package_type != '':
            response = Packages.GetPackagesDetails(
                is_jpl=is_jpl,
                owner=owner,
                package_name=package_name,
                package_type=package_type)
            json_data_info = json.loads(response.text)
            for elem in json_data_info:
                tags = elem['metadata']['container']['tags']
                if env.name.lower() in tags:
                    print(f'Found Information:\r\n{elem}')
                    version = ''
                    # Get the version tag and ignore the 'latest' and the 'env' tag
                    for tag in tags:
                        if tag in [env.name.lower(), 'latest']:
                            continue
                        version = tag
                    url = f'{elem["html_url"]}?tag={version}'
                    return url
        return package_name


    def GetDocumentationLink(repo_link: str) -> str:
        '''Function to generate the documentation link'''

        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link=repo_link)
        url = f'https://podaac.github.io/{repo_name}'
        raw_page_content = WebUtils.GetUrl(url)
        do_exists = 'Site not found' not in raw_page_content and 'a GitHub Pages site here.' not in raw_page_content
        if do_exists:
            return url
        return f'No Documentation present at "{url}"!'


    def GetDocumentationVersion(repo_link: str) -> str:
        '''Function to check the documentation version'''

        from data_updater.distributor import Distributor
        result = Distributor.GetDocumentationLink(repo_link)
        if 'no documentation' not in result.lower():
            raw_page_content = WebUtils.GetUrl(result)
            pattern = r'<div\s+class=.version.+\s+([0-9a-zA-Z.]+)'
            mo = re.findall(pattern=pattern, string=raw_page_content)
            if len(mo) > 0:
                result = mo[-1]
            else:
                result = 'No Version found on the document page!'
        return result


    def GenerateGHCRLink(repo_link: str, environment: str) -> str:
        '''Function to create the GHCR link of the Github repository published to Docker'''

        from data_updater.distributor import Distributor
        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        (package_name, package_type) = GitHubUtils.GetPackageDetails(is_jpl=is_jpl, owner=owner, repo_link=repo_link)
        result = package_name
        if package_type == 'container':
            version = Distributor.GetGithubPackageVersionTag(repo_link=repo_link, environment=environment)
            result = f'ghcr.io/{owner}/{package_name}:{version}'
        return result


    def GeneratePyPiReleaseLink(repo_link: str, environment: str) -> str:
        '''Function to create the PyPi link of the Github repository from the poetry file found in the repository'''

        # Get the Poetry toml file content from the repository
        poetry_file_name = 'pyproject.toml'
        (is_jpl, owner, repo_name) = GitHubUtils.ExtractRepoData(repo_link)
        if is_jpl:
            return 'API does not exists!'
        file_content = Contents.GetDecodedFileContent(
            is_jpl=is_jpl,
            owner=owner,
            repo_name=repo_name,
            file_path=poetry_file_name)
        if 'not found' in file_content:
            return file_content

        # Extract the project name from the file
        pattern = r'name\s=\s"([a-zA-Z0-9-_.,]+)"'
        mo = re.findall(pattern=pattern, string=file_content)
        if mo is not None and len(mo) > 0:
            poetry_project_name = mo[-1]
        else:
            print(f'\r\nRaw Data:\r\n{file_content}')
            print(f'Mo: {mo}')
            return 'Project name is not found in the file!'

        # Generate the PyPi url with the extracted project name
        if environment.lower() in ['ops']:
            url = f'https://pypi.org/project/{poetry_project_name}'
        elif environment.lower() in ['uat']:
            url = f'https://test.pypi.org/project/{poetry_project_name}'
        else:
            raise NotImplementedError(f'Url is not defined for environment "{environment.lower()}"')

        # Check if the url exists
        raw_page_content = WebUtils.GetUrl(url)
        do_exists = 'we looked everywhere but couldn\'t find this page' not in raw_page_content.lower()
        if do_exists:
            return url
        return f'PyPi page is not found at "{url}"!'
