import os
import requests
import gspread
from bs4 import BeautifulSoup

gc = gspread.service_account()

spreadsheet_id = os.environ['SPREADSHEET_ID']

workbook = gc.open_by_key(spreadsheet_id)

repos_sheet = workbook.worksheet("Repos")


def get_open_count(repo_name, github_token, count_type):
    """
    Returns the number of open pull requests or issues for a given GitHub repository.

    Parameters:
    repo_name (str): The repository name in the format "owner/repo".
    github_token (str): Your GitHub personal access token.
    count_type (str): The type of count to retrieve, either "pr" for pull requests or "issue" for issues.

    Returns:
    int: The number of open pull requests or issues.
    """
    if count_type not in ["pr", "issue"]:
        raise ValueError("Invalid count_type. Use 'pr' for pull requests or 'issue' for issues.")

    url = "https://api.github.com/search/issues"  # search/issues is used for both issues and PRs
    query = f"repo:{repo_name} is:{count_type} is:open"
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


def get_latest_releases(repo_name):
    """
    Returns the latest final release and the latest prerelease containing "rc" in the tag name
    for a given GitHub repository.

    Parameters:
    repo_name (str): The repository name in the format "owner/repo".

    Returns:
    dict: A dictionary with keys "latest_final" and "latest_rc", containing the corresponding tag names.
    """
    url = f"https://api.github.com/repos/{repo_name}/releases"

    try:
        response = requests.get(url)
        response.raise_for_status()
        releases = response.json()

        latest_final = None
        latest_rc = None

        for release in releases:
            tag_name = release["tag_name"]
            if not release["prerelease"]:  # Final release
                if latest_final is None:
                    latest_final = tag_name
            elif "rc" in tag_name.lower():  # Prerelease containing "rc"
                if latest_rc is None:
                    latest_rc = tag_name

            # Stop searching if both are found
            if latest_final and latest_rc:
                break

        return {"latest_final": latest_final, "latest_rc": latest_rc}

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    return {"latest_final": None, "latest_rc": None}


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


def get_webpage_title(url):
    """
    Fetches the title of a web page given its URL.

    Parameters:
        url (str): The URL of the web page.

    Returns:
        str: The title of the web page, or an error message if unavailable.
    """
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the title tag
        title = soup.title.string if soup.title else "Title not found"
        return title.strip() if title else "Title is empty"

    except requests.exceptions.RequestException as e:
        return None


def get_repos():
    """Get the list of repositories from the spreadsheet"""

    repo_list = []

    repo_table = repos_sheet.get_all_values()

    col_index = 1
    for index, col in enumerate(repo_table[0]):
        if col == 'JPL GitHub':
            col_index = index
            break

    for index, row in enumerate(repo_table[2:]):
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
                pr_count = get_open_count(repo_name, github_token, "pr")
            #    issue_count = get_open_count(repo_name, github_token, "issue")

                releases = get_latest_releases(repo_name)
                print("Releases: ")
                print(releases)
                
                final_release = releases.get("latest_final", "")
                rc_release = releases.get("latest_rc", "")

                ops_package = ""
                uat_package = ""

                versions = get_all_tagged_package_versions(repo_name, github_token)
                if versions:
                    print("Package Versions:")
                    for version in versions:
                        if 'ops' in version['metadata']['container']['tags']:
                            ops_package = version['metadata']['container']['tags'][0]
                        if 'uat' in version['metadata']['container']['tags']:
                            uat_package = version['metadata']['container']['tags'][0]

                        print(f"Version ID: {version['id']}, Tags: {version['metadata']['container']['tags']}")

                # Get Gibhub.io docs version
                name = repo_name.split("/")[-1]
                title = get_webpage_title(f"https://podaac.github.io/{name}/")
                print(f"Title: {title}")

                docs_version = ""
                if title:
                    title_words = title.split()
                    docs_version = title_words[-2] if len(title_words) > 1 else None

                row.append(pr_count)
                row.append("")
                row.append(final_release)
                row.append(rc_release)
                row.append(ops_package)
                row.append(uat_package)
                row.append(docs_version)
            else:
                row.append("")
                row.append("")
                row.append("")
                row.append("")
                row.append("")
                row.append("")
        except Exception as ex:
            print(ex)

        new_table.append(row)

    repos_sheet.update(new_table, 'C3')


    # Example usage:
    repo_name = "podaac/forge-py"
    open_pr_count = get_open_count(repo_name, github_token, "pr")
    print(f"Open PR count for {repo_name}: {open_pr_count}")

    releases = get_latest_releases(repo_name)
    print(f"Releases for {repo_name}: {releases}")

    versions = get_all_tagged_package_versions(repo_name, github_token)
    if versions:
        print("Package Versions:")
        for version in versions:
            print(f"Version ID: {version['id']}, Tags: {version['metadata']['container']['tags']}")

if __name__ == "__main__":
    main()
