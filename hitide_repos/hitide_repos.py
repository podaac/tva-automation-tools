import os
import requests
import gspread

gc = gspread.service_account()

spreadsheet_id = os.environ['SPREADSHEET_ID']

workbook = gc.open_by_key(spreadsheet_id)

repos_sheet = workbook.worksheet("Repos")


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
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
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
        return ""


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

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return ""


def get_all_tagged_package_versions(repo_name, token):
    owner, package_name = repo_name.split("/")
    versions_url = f"https://api.github.com/orgs/{owner}/packages/container/{package_name}/versions"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    all_tagged_versions = []
    page = 1

    # Loop through all pages to get all versions
    while True:
        response = requests.get(versions_url, headers=headers, params={"page": page, "per_page": 100})
        if response.status_code != 200:
            print(f"Failed to retrieve package versions: {response.status_code}")
            return None

        versions = response.json()
        if not versions:
            break  # Exit loop if there are no more versions

        # Filter versions to include only those with tags
        tagged_versions = [
            version for version in versions
            if 'tags' in version['metadata']['container'] and version['metadata']['container']['tags']
        ]

        all_tagged_versions.extend(tagged_versions)
        page += 1

    return all_tagged_versions


def get_repos():
    """Get the list of repositories from the spreadsheet"""

    repo_list = []

    repo_table = repos_sheet.get_all_values()

    col_index = 1
    for index, col in enumerate(repo_table[0]):
        if col == 'JPL GitHub':
            col_index = index
            break

    for index, row in enumerate(repo_table[1:]):
        repo = {"name": row[0],
                "jpl_github": row[col_index] == 'X'}
        repo_list.append(repo)

    return repo_list


def main():
    """ Update HiTIDE DevOps Repos Google Sheet"""

    repos = get_repos()

    print(repos)

    github_token = os.environ['GITHUB_TOKEN']

    new_table = []
    for repo in repos:
        row = []

        try:
            repo_name = "podaac/" + repo.get('name') if '/' not in repo.get('name') else repo.get('name')
            jpl_github = repo.get('jpl_github')

            print("Repo: " + repo_name)
            if not jpl_github:
                pr_count = get_open_pr_count(repo_name, github_token)
                latest_release = get_latest_release(repo_name)

                row.append(pr_count)
                row.append(latest_release)
            else:
                row.append("")
                row.append("")
        except Exception as ex:
            print(ex)

        new_table.append(row)

    repos_sheet.update(new_table, 'C2')


    # Example usage:
    repo_name = "podaac/forge-py"
    open_pr_count = get_open_pr_count(repo_name, github_token)
    print(f"Open PR count for {repo_name}: {open_pr_count}")

    latest_release = get_latest_release(repo_name)
    print(f"Latest release for {repo_name}: {latest_release}")

    versions = get_all_tagged_package_versions(repo_name, github_token)
    if versions:
        print("Package Versions:")
        for version in versions:
            print(f"Version ID: {version['id']}, Tags: {version['metadata']['container']['tags']}")

if __name__ == "__main__":
    main()
