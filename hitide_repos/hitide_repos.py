from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Lock
import os
import pytz
from datetime import datetime
import gspread
import requests

from retrying import retry


gc = gspread.service_account()

lock = Lock()

spreadsheet_id = os.environ['SPREADSHEET_ID']

workbook = gc.open_by_key(spreadsheet_id)

now = datetime.now(pytz.timezone('US/Pacific'))
current_month = now.strftime("%Y-%m")

# Now, create or open a worksheet in the spreadsheet
worksheet_title = "Repos"

repos_sheet = workbook.worksheet(worksheet_title)


import requests

def get_open_pr_count(repo_name, github_token):
    """
    Returns the number of open pull requests for a given GitHub repository.

    Parameters:
    repo_name (str): The repository name in the format "owner/repo".
    token (str): Your GitHub personal access token.

    Returns:
    int: The number of open pull requests.
    """
    url = "https://api.github.com/search/issues"
    query = f"repo:{repo_name} is:pr is:open"
    headers = {
        "Authorization": f"Bearer {github_token}"
    }

    params = {
        "q": query
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data["total_count"]
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_latest_release(repo_name):
    """
    Returns the latest release version (excluding pre-releases) for a given GitHub repository.

    Parameters:
    repo_name (str): The repository name in the format "owner/repo".

    Returns:
    str: The tag name of the latest release, or None if there are no releases.
    """
    url = f"https://api.github.com/repos/{repo_name}/releases"

    try:
        response = requests.get(url)
        response.raise_for_status()
        releases = response.json()

        # Filter out pre-releases and return the first release found
        for release in releases:
            if not release["prerelease"]:
                return release["tag_name"]

        return "No non-pre-release versions found"
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def get_repos():

    repo_list = []

    repo_table = repos_sheet.get_all_values()
    
    for index, row in enumerate(repo_table[1:]):
        repo_list.append(row[0])

    return repo_list


def main(args=None):
    
    print("Hello World!")

    repos = get_repos()

    print(repos)

    github_token = os.environ['GITHUB_TOKEN']

    new_table = []
    for repo in repos:
        row = [repo]

        print("Repo: " + repo)
        row.append(get_open_pr_count("podaac/" + repo, github_token))
        row.append(get_latest_release("podaac/" + repo))

        new_table.append(row)


    repos_sheet.update(new_table, 'B2')


    # Example usage:
    repo_name = "podaac/forge-py"
    open_pr_count = get_open_pr_count(repo_name, github_token)
    print(f"Open PR count for {repo_name}: {open_pr_count}")

    latest_release = get_latest_release(repo_name)
    print(f"Latest release for {repo_name}: {latest_release}")


if __name__ == "__main__":
    main()
