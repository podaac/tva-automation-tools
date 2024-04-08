"""Github module"""


class Git():
    """Class for Github related methods"""

    def GetGitPackageVersionTag(environment:str) -> str:
        """Function to get the package version of the git repository with the tag of environment"""
        raise NotImplementedError()


    def GetGitOpenPRCount() -> int:
        """Function to get the open pull requests count of the git repository"""
        raise NotImplementedError()


    def GetGitOpenIssueCount() -> int:
        """Function to get the open issues count of the git repository"""
        raise NotImplementedError()


    def GetGitLastActionStatus(branches:list[str]) -> bool:
        """Function to get the status of the last action ran on any of the provided branches of the git repository"""
        raise NotImplementedError()


    def GetGitFailedActionCount(daysToCheck:str) -> int:
        """Function to get the count of the failed action ran
            on any of the provided branches of the git repository
            in the past x days"""
        raise NotImplementedError()


    def GetGitPackageLinkWithTag(environment:str) -> str:
        """Function to get the package link of the git repository with the tag of environment"""
        raise NotImplementedError()
