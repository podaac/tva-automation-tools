"""Github module"""
# pylint: disable=W0612
# W0612 => to ignore unused tuple 3rd element

from datetime import datetime, timedelta
import json

from API.Github import Actions, Issues, Packages, PullRequests
from enums import Environment


class Github():
    """Class for Github related methods"""

    def GetGithubOpenPRCount(repoLink:str) -> int:
        """Function to get the open pull requests count of the github repository"""

        (is_jpl, owner, repo_name) = ExtractRepoData(repoLink)
        if is_jpl:
            return "API does not exists!"
        response = PullRequests.GetPullRequests(
            isJpl = is_jpl,
            owner = owner,
            repoName = repo_name)
        json_data = json.loads(response.text)
        count = 0
        for elem in json_data:
            if elem['state'] == 'open':
                count += 1
        return count


    def GetGithubOpenIssueCount(repoLink:str) -> int:
        """Function to get the open issues count of the github repository"""

        (is_jpl, owner, repo_name) = ExtractRepoData(repoLink)
        if is_jpl:
            return "API does not exists!"
        response = Issues.GetIssues(
            isJpl = is_jpl,
            owner = owner,
            repoName = repo_name)
        json_data = json.loads(response.text)
        count = 0
        for elem in json_data:
            if elem['state'] == 'open':
                count += 1
        return count


    def GetGithubLastActionStatus(repoLink:str, branches:list[str]) -> str:
        """Function to get the status of the last action ran on any of the provided branches of the github repository"""

        (is_jpl, owner, repo_name) = ExtractRepoData(repoLink)
        if is_jpl:
            return "API does not exists!"
        response = Actions.GetWorkflowRuns(
            isJpl = is_jpl,
            owner = owner,
            repoName = repo_name)
        json_data = json.loads(response.text)
        most_recent_run = ""
        result = json_data['workflow_runs'][0]['updated_at']
        for elem in json_data['workflow_runs']:
            if elem['head_branch'] in branches and elem['status'] == 'completed' and elem['updated_at'] >= most_recent_run:
                print('\r\nFound a new one!...')
                result = elem['conclusion']
                most_recent_run = elem['updated_at']
                print(f"result: {result}")
                print(f"updated_at: {most_recent_run}")

        return result


    def GetGithubFailedActionCount(repoLink:str, daysToCheck:str, branches:list[str]) -> int:
        """Function to get the count of the failed action ran
            on any of the provided branches of the github repository
            in the past x days"""

        days_to_check = int(daysToCheck)
        (is_jpl, owner, repo_name) = ExtractRepoData(repoLink)
        if is_jpl:
            return "API does not exists!"
        response = Actions.GetWorkflowRuns(
            isJpl = is_jpl,
            owner = owner,
            repoName = repo_name)
        json_data = json.loads(response.text)
        time_of_last = datetime.fromisoformat(json_data['workflow_runs'][0]['updated_at'][:-1])
        time_interval = time_of_last - timedelta(days = days_to_check)
        count = 0
        for elem in json_data['workflow_runs']:
            if elem['head_branch'] in branches and elem['status'] == 'completed' and elem['updated_at'] >= time_interval.isoformat() and elem['conclusion'] == "failure":
                count += 1
        return count


    def GetGithubPackageVersionTag(repoLink:str, environment:str) -> str:
        """Function to get the package version of the github repository with the tag of environment"""

        env = Environment.FromStr(environment)
        (is_jpl, owner, repo_name) = ExtractRepoData(repoLink)
        if is_jpl:
            return "API does not exists!"
        (package_name, package_type) = GetPackageDetails(isJpl = is_jpl, owner = owner, repoLink = repoLink)
        if package_type != "":
            response = Packages.GetPackagesDetails(
                isJpl = is_jpl,
                owner = owner,
                packageName = package_name,
                packageType = package_type)
            json_data = json.loads(response.text)
            for elem in json_data:
                tags = elem['metadata']['container']['tags']
                if env.name.lower() in tags:
                    for tag in tags:
                        if tag in [env.name.lower(), 'latest']:
                            continue
                        return tag
        return package_name


    def GetGithubPackageLinkWithTag(repoLink:str, environment:str) -> str:
        """Function to get the package link of the github repository with the tag of environment"""

        env = Environment.FromStr(environment)
        (is_jpl, owner, repo_name) = ExtractRepoData(repoLink = repoLink)
        if is_jpl:
            return "API does not exists!"
        (package_name, package_type) = GetPackageDetails(isJpl = is_jpl, owner = owner, repoLink = repoLink)
        if package_type != "":
            response = Packages.GetPackagesDetails(
                isJpl = is_jpl,
                owner = owner,
                packageName = package_name,
                packageType = package_type)
            json_data_info = json.loads(response.text)
            for elem in json_data_info:
                print(f'elem:\r\n{elem}')
                tags = elem['metadata']['container']['tags']
                if env.name.lower() in tags:
                    url = elem['html_url']
                    return url
        return package_name


def GetPackageDetails(isJpl:bool, owner:str, repoLink:str) -> tuple:
    """Function to extract name and type information of package of the repository"""

    response = Packages.GetPackages(
            isJpl = isJpl,
            owner = owner)
    json_data_list = json.loads(response.text)
    package_name = "Package Not Found!"
    package_type = ""
    for package in json_data_list:
        if 'repository' not in package:
            continue
        if package['repository']['html_url'] == repoLink:
            package_name = package['name']
            package_type = package['package_type']
            print(f'\r\npackage_name: {package_name}')
            print(f'package_type: {package_type}\r\n')
            break
    return (package_name, package_type)


def ExtractRepoData(repoLink:str) -> tuple:
    """Function to extract information from repository link"""

    github_base = "https://github.com"
    github_jpl_base = "https://github.jpl.nasa.gov"
    is_jpl = None
    if repoLink.startswith(github_jpl_base):
        is_jpl = True
        repoLink = repoLink.removeprefix(f'{github_jpl_base}/')
    elif repoLink.startswith(github_base):
        is_jpl = False
        repoLink = repoLink.removeprefix(f'{github_base}/')
    else:
        raise NotImplementedError(f'"{repoLink}" not an Github address!')

    values = repoLink.split('/')
    print(f'isJpl: {is_jpl}')
    print(f'owner: {values[0]}')
    print(f'repo_name: {values[1]}\r\n')
    return (is_jpl, values[0], values[1])
