"""Task Distributor module"""

from data_updater import AWS, Cumulus, Docker, Git, Harmony, PyPi


class Distributor():
    """Class to able to use getattr"""

    def GetAwsDeployedVersion(environment:str) -> str:
        """Function to call GetAwsDeployedVersion"""
        return "Under development"
        return AWS.GetAwsDeployedVersion(environment = environment)


    def GetAwsLambdaImage() -> str:
        """Function to call GetAwsLambdaImage"""
        return "Under development"
        return AWS.GetAwsLambdaImage()


    def GetAwsLambdaName() -> str:
        """Function to call GetAwsLambdaName"""
        return "Under development"
        return AWS.GetAwsLambdaName()


    def GetGitPackageVersionTag(environment:str) -> str:
        """Function to call GetGitPackageVersionTag"""
        return "Under development"
        return Git.GetGitPackageVersionTag(environment = environment)


    def GetGitOpenPRCount() -> int:
        """Function to call GetGitOpenPRCount"""
        return "Under development"
        return Git.GetGitOpenPRCount()


    def GetGitOpenIssueCount() -> int:
        """Function to call GetGitOpenIssueCount"""
        return "Under development"
        return Git.GetGitOpenIssueCount()


    def GetGitLastActionStatus(branches:list[str]) -> bool:
        """Function to call GetGitLastActionStatus"""
        return "Under development"
        return Git.GetGitLastActionStatus(branches = branches)


    def GetGitFailedActionCount(daysToCheck:str) -> int:
        """Function to call GetGitFailedActionCount"""
        return "Under development"
        return Git.GetGitFailedActionCount(daysToCheck = daysToCheck)


    def GetGitPackageLinkWithTag(environment:str) -> str:
        """Function to call GetGitPackageLinkWithTag"""
        return "Under development"
        return Git.GetGitPackageLinkWithTag(environment = environment)


    def GetDockerPackageLink(environment:str) -> str:
        """Function to call GetDockerPackageLink"""
        return "Under development"
        return Docker.GetDockerPackageLink(environment = environment)


    def GetPyPiReleaseLink(environment:str) -> str:
        """Function to call GetPyPiReleaseLink"""
        return "Under development"
        return PyPi.GetPyPiReleaseLink(environment = environment)


    def GetCumulusReleaseLink(environment:str) -> str:
        """Function to call GetCumulusReleaseLink"""
        return "Under development"
        return Cumulus.GetCumulusReleaseLink(environment = environment)


    def GetVersionFromHarmony(environment:str, serviceName:str) -> str:
        """Function to call GetHarmonyVersion"""
        return Harmony.GetVersionFromHarmony(
            serviceName = serviceName,
            environment = environment)
