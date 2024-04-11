"""Task Distributor module"""

from data_updater import AWS, Cumulus, Docker, Github, Harmony, PyPi


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


    def GetGithubPackageVersionTag(repoLink:str, environment:str) -> str:
        """Function to call GetGithubPackageVersionTag"""
        return Github.GetGithubPackageVersionTag(
            repoLink = repoLink,
            environment = environment)


    def GetGithubOpenPRCount(repoLink:str) -> int:
        """Function to call GetGithubOpenPRCount"""
        return Github.GetGithubOpenPRCount(repoLink = repoLink)


    def GetGithubOpenIssueCount(repoLink:str) -> int:
        """Function to call GetGithubOpenIssueCount"""
        return Github.GetGithubOpenIssueCount(repoLink = repoLink)


    def GetGithubLastActionStatus(repoLink:str, branches:list[str]) -> bool:
        """Function to call GetGithubLastActionStatus"""
        return Github.GetGithubLastActionStatus(
            repoLink = repoLink,
            branches = branches)


    def GetGithubFailedActionCount(repoLink:str, daysToCheck:str, branches:list[str]) -> int:
        """Function to call GetGithubFailedActionCount"""
        return Github.GetGithubFailedActionCount(
            repoLink = repoLink,
            daysToCheck = daysToCheck,
            branches = branches)


    def GetGithubPackageLinkWithTag(repoLink:str, environment:str) -> str:
        """Function to call GetGithubPackageLinkWithTag"""
        return Github.GetGithubPackageLinkWithTag(
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
