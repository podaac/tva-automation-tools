'''Task Distributor module'''
# pylint: disable=E1120
# E1120 => All parameters have input values...

from data_updater import AWS, Cumulus, Github, Harmony, PyPi
import config.config


# File wide variables
CONF = config.Config


class Distributor():
    '''Class to able to use getattr'''

    def GetAwsDeployedVersion(environment: str) -> str:
        '''Function to call GetAwsDeployedVersion'''

        result = Wrapper(
            methoToExecute=AWS.GetAwsDeployedVersion,
            arguments=[environment],
            methodName='GetAwsDeployedVersion',
            levelOne=environment)
        return result


    def GetAwsLambdaImage() -> str:
        '''Function to call GetAwsLambdaImage'''

        result = Wrapper(
            methoToExecute=AWS.GetAwsLambdaImage,
            arguments=[],
            methodName='GetAwsLambdaImage')
        return result


    def GetAwsLambdaName() -> str:
        '''Function to call GetAwsLambdaName'''

        result = Wrapper(
            methoToExecute=AWS.GetAwsLambdaName,
            arguments=[],
            methodName='GetAwsLambdaName')
        return result


    def GetGithubPackageVersionTag(repoLink: str, environment: str) -> str:
        '''Function to call GetGithubPackageVersionTag'''
        result = Wrapper(
            methoToExecute=Github.GetGithubPackageVersionTag,
            arguments=[repoLink, environment],
            methodName='GetGithubPackageVersionTag',
            levelOne=environment)
        return result


    def GetGithubOpenPRCount(repoLink: str) -> int:
        '''Function to call GetGithubOpenPRCount'''

        result = Wrapper(
            methoToExecute=Github.GetGithubOpenPRCount,
            arguments=[repoLink],
            methodName='GetGithubOpenPRCount')
        return result


    def GetGithubOpenIssueCount(repoLink: str) -> int:
        '''Function to call GetGithubOpenIssueCount'''

        result = Wrapper(
            methoToExecute=Github.GetGithubOpenIssueCount,
            arguments=[repoLink],
            methodName='GetGithubOpenIssueCount')
        return result


    def GetGithubLastActionStatus(repoLink: str, branches: list[str]) -> bool:
        '''Function to call GetGithubLastActionStatus'''

        result = Wrapper(
            methoToExecute=Github.GetGithubLastActionStatus,
            arguments=[repoLink, branches],
            methodName='GetGithubLastActionStatus')
        return result


    def GetGithubFailedActionCount(repoLink: str, daysToCheck: str, branches: list[str]) -> int:
        '''Function to call GetGithubFailedActionCount'''

        result = Wrapper(
            methoToExecute=Github.GetGithubFailedActionCount,
            arguments=[repoLink, daysToCheck, branches],
            methodName='GetGithubFailedActionCount')
        return result


    def GetGithubPackageLinkWithTag(repoLink: str, environment: str) -> str:
        '''Function to call GetGithubPackageLinkWithTag'''

        result = Wrapper(
            methoToExecute=Github.GetGithubPackageLinkWithTag,
            arguments=[repoLink, environment],
            methodName='GetGithubPackageLinkWithTag',
            levelOne=environment)
        return result



    def GenerateGHCRLink(repoLink: str, environment: str) -> str:
        '''Function to call GenerateGHCRLink'''

        result = Wrapper(
            methoToExecute=Github.GenerateGHCRLink,
            arguments=[repoLink, environment],
            methodName='GenerateGHCRLink',
            levelOne=environment)
        return result


    def GeneratePyPiReleaseLink(repoLink: str, environment: str) -> str:
        '''Function to call GeneratePyPiReleaseLink'''

        result = Wrapper(
            methoToExecute=Github.GeneratePyPiReleaseLink,
            arguments=[repoLink, environment],
            methodName='GeneratePyPiReleaseLink',
            levelOne=environment)
        return result


    def GetPyPiVersion(repoLink: str, environment: str) -> str:
        '''Function to call GetPyPiVersion'''

        result = Wrapper(
            methoToExecute=PyPi.GetPyPiVersion,
            arguments=[repoLink, environment],
            methodName='GetPyPiVersion',
            levelOne=environment)
        return result


    def GetCumulusReleaseLink(environment: str) -> str:
        '''Function to call GetCumulusReleaseLink'''

        result = Wrapper(
            methoToExecute=Cumulus.GetCumulusReleaseLink,
            arguments=[environment],
            methodName='GetCumulusReleaseLink',
            levelOne=environment)
        return result


    def GetVersionFromHarmony(environment: str, serviceName: str = '') -> str:
        '''Function to call GetHarmonyVersion'''

        if serviceName == '':
            result = 'No service defined!'
        else:
            result = Wrapper(
                methoToExecute=Harmony.GetVersionFromHarmony,
                arguments=[environment, serviceName],
                methodName='GetVersionFromHarmony',
                levelOne=environment)
        return result


    def GetDocumentationLink(repoLink: str) -> str:
        '''Function to get the documentation link for the repository'''

        result = Wrapper(
            methoToExecute=Github.GetDocumentationLink,
            arguments=[repoLink],
            methodName='GetDocumentationLink')
        return result


    def GetDocumentationVersion(repoLink: str) -> str:
        '''Function to get the documentation version for the repository'''

        result = Wrapper(
            methoToExecute=Github.GetDocumentationVersion,
            arguments=[repoLink],
            methodName='GetDocumentationVersion')
        return result


def Wrapper(methoToExecute, arguments: list, methodName: str, levelOne: str = 'all'):
    '''Function to store data found or reuse already extracted data'''

    if methodName not in CONF.VAR_DataExtracted:
        CONF.VAR_DataExtracted[methodName] = {}
    if levelOne not in CONF.VAR_DataExtracted[methodName]:
        # Execute action here
        if len(arguments) == 0:
            result = methoToExecute()
        elif len(arguments) == 1:
            result = methoToExecute(arguments[0])
        elif len(arguments) == 2:
            result = methoToExecute(arguments[0], arguments[1])
        elif len(arguments) == 3:
            result = methoToExecute(arguments[0], arguments[1], arguments[2])
        CONF.VAR_DataExtracted[methodName][levelOne] = result
    else:
        print('Result found from previous execution, using stored data!')
        result = CONF.VAR_DataExtracted[methodName][levelOne]
    return result
