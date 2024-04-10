"""Task Distributor module"""

from data_updater import AWS, Cumulus, Docker, Git, Harmony, PyPi


class Distributor():
    """Class to able to use getattr"""

    def GetAwsDeployedVersion(environment:str) -> str:
        """Function to call GetAwsDeployedVersion"""
        return AWS.GetAwsDeployedVersion(environment = environment)


    def GetAwsLambdaImage() -> str:
        """Function to call GetAwsLambdaImage"""
        return AWS.GetAwsLambdaImage()


    def GetAwsLambdaName() -> str:
        """Function to call GetAwsLambdaName"""
        return AWS.GetAwsLambdaName()


    def GetGitPackageVersionTag(repoLink:str, environment:str) -> str:
        """Function to call GetGitPackageVersionTag"""
        return Git.GetGitPackageVersionTag(
            repoLink = repoLink,
            environment = environment)


    def GetGitOpenPRCount(repoLink:str) -> int:
        """Function to call GetGitOpenPRCount"""
        return Git.GetGitOpenPRCount(repoLink = repoLink)


    def GetGitOpenIssueCount(repoLink:str) -> int:
        """Function to call GetGitOpenIssueCount"""
        return Git.GetGitOpenIssueCount(repoLink = repoLink)


    def GetGitLastActionStatus(repoLink:str, branches:list[str]) -> bool:
        """Function to call GetGitLastActionStatus"""
        return Git.GetGitLastActionStatus(
            repoLink = repoLink,
            branches = branches)


    def GetGitFailedActionCount(repoLink:str, daysToCheck:str, branches:list[str]) -> int:
        """Function to call GetGitFailedActionCount"""
        return Git.GetGitFailedActionCount(
            repoLink = repoLink,
            daysToCheck = daysToCheck,
            branches = branches)


    def GetGitPackageLinkWithTag(repoLink:str, environment:str) -> str:
        """Function to call GetGitPackageLinkWithTag"""
        return Git.GetGitPackageLinkWithTag(
            repoLink = repoLink,
            environment = environment)


    def GetDockerPackageLink(environment:str) -> str:
        """Function to call GetDockerPackageLink"""
        return Docker.GetDockerPackageLink(environment = environment)


    def GetPyPiReleaseLink(environment:str) -> str:
        """Function to call GetPyPiReleaseLink"""
        return PyPi.GetPyPiReleaseLink(environment = environment)


    def GetCumulusReleaseLink(environment:str) -> str:
        """Function to call GetCumulusReleaseLink"""
        return Cumulus.GetCumulusReleaseLink(environment = environment)


    def GetVersionFromHarmony(environment:str, serviceName:str="") -> str:
        """Function to call GetHarmonyVersion"""
        if serviceName == "":
            return "No service defined!"
        return Harmony.GetVersionFromHarmony(
            serviceName = serviceName,
            environment = environment)


    def GetDocumentationLink() -> str:
        """Function to get the documentation link for the repository"""

        return "Under development"


    def GetDocumentationVersoin() -> str:
        """Function to get the documentation version for the repository"""

        return "Under development"
