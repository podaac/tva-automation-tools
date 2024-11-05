'''Task Distributor module'''
# pylint: disable=E1120
# E1120 => All parameters have input values...

from data_updater import AWS, Cumulus, Github, Harmony, PyPi
import config.config


# Constants
CONF = config.Config


class Distributor():
    '''Class to able to use getattr'''

    def GetAwsDeployedVersion(environment: str) -> str:
        '''Function to call GetAwsDeployedVersion'''

        result = Wrapper(
            metho_to_execute=AWS.GetAwsDeployedVersion,
            arguments=[environment],
            method_name='GetAwsDeployedVersion',
            level_one=environment)
        return result


    def GetAwsLambdaImage() -> str:
        '''Function to call GetAwsLambdaImage'''

        result = Wrapper(
            metho_to_execute=AWS.GetAwsLambdaImage,
            arguments=[],
            method_name='GetAwsLambdaImage')
        return result


    def GetAwsLambdaName() -> str:
        '''Function to call GetAwsLambdaName'''

        result = Wrapper(
            metho_to_execute=AWS.GetAwsLambdaName,
            arguments=[],
            method_name='GetAwsLambdaName')
        return result


    def GetGithubPackageVersionTag(repo_link: str, environment: str) -> str:
        '''Function to call GetGithubPackageVersionTag'''
        result = Wrapper(
            metho_to_execute=Github.GetGithubPackageVersionTag,
            arguments=[repo_link, environment],
            method_name='GetGithubPackageVersionTag',
            level_one=environment)
        return result


    def GetGithubOpenPRCount(repo_link: str) -> int:
        '''Function to call GetGithubOpenPRCount'''

        result = Wrapper(
            metho_to_execute=Github.GetGithubOpenPRCount,
            arguments=[repo_link],
            method_name='GetGithubOpenPRCount')
        return result


    def GetGithubOpenIssueCount(repo_link: str) -> int:
        '''Function to call GetGithubOpenIssueCount'''

        result = Wrapper(
            metho_to_execute=Github.GetGithubOpenIssueCount,
            arguments=[repo_link],
            method_name='GetGithubOpenIssueCount')
        return result


    def GetGithubLastActionStatus(repo_link: str, branches: list[str]) -> bool:
        '''Function to call GetGithubLastActionStatus'''

        result = Wrapper(
            metho_to_execute=Github.GetGithubLastActionStatus,
            arguments=[repo_link, branches],
            method_name='GetGithubLastActionStatus')
        return result


    def GetGithubFailedActionCount(repo_link: str, days_to_check: str, branches: list[str]) -> int:
        '''Function to call GetGithubFailedActionCount'''

        result = Wrapper(
            metho_to_execute=Github.GetGithubFailedActionCount,
            arguments=[repo_link, days_to_check, branches],
            method_name='GetGithubFailedActionCount')
        return result


    def GetGithubPackageLinkWithTag(repo_link: str, environment: str) -> str:
        '''Function to call GetGithubPackageLinkWithTag'''

        result = Wrapper(
            metho_to_execute=Github.GetGithubPackageLinkWithTag,
            arguments=[repo_link, environment],
            method_name='GetGithubPackageLinkWithTag',
            level_one=environment)
        return result



    def GenerateGHCRLink(repo_link: str, environment: str) -> str:
        '''Function to call GenerateGHCRLink'''

        result = Wrapper(
            metho_to_execute=Github.GenerateGHCRLink,
            arguments=[repo_link, environment],
            method_name='GenerateGHCRLink',
            level_one=environment)
        return result


    def GeneratePyPiReleaseLink(repo_link: str, environment: str) -> str:
        '''Function to call GeneratePyPiReleaseLink'''

        result = Wrapper(
            metho_to_execute=Github.GeneratePyPiReleaseLink,
            arguments=[repo_link, environment],
            method_name='GeneratePyPiReleaseLink',
            level_one=environment)
        return result


    def GetPyPiVersion(repo_link: str, environment: str) -> str:
        '''Function to call GetPyPiVersion'''

        result = Wrapper(
            metho_to_execute=PyPi.GetPyPiVersion,
            arguments=[repo_link, environment],
            method_name='GetPyPiVersion',
            level_one=environment)
        return result


    def GetCumulusReleaseLink(environment: str) -> str:
        '''Function to call GetCumulusReleaseLink'''

        result = Wrapper(
            metho_to_execute=Cumulus.GetCumulusReleaseLink,
            arguments=[environment],
            method_name='GetCumulusReleaseLink',
            level_one=environment)
        return result


    def GetVersionFromHarmony(environment: str, service_name: str = '') -> str:
        '''Function to call GetHarmonyVersion'''

        if service_name == '':
            result = 'No service defined!'
        else:
            result = Wrapper(
                metho_to_execute=Harmony.GetVersionFromHarmony,
                arguments=[environment, service_name],
                method_name='GetVersionFromHarmony',
                level_one=environment)
        return result


    def GetDocumentationLink(repo_link: str) -> str:
        '''Function to get the documentation link for the repository'''

        result = Wrapper(
            metho_to_execute=Github.GetDocumentationLink,
            arguments=[repo_link],
            method_name='GetDocumentationLink')
        return result


    def GetDocumentationVersion(repo_link: str) -> str:
        '''Function to get the documentation version for the repository'''

        result = Wrapper(
            metho_to_execute=Github.GetDocumentationVersion,
            arguments=[repo_link],
            method_name='GetDocumentationVersion')
        return result


def Wrapper(metho_to_execute, arguments: list, method_name: str, level_one: str = 'all'):
    '''Function to store data found or reuse already extracted data'''

    if method_name not in CONF.VAR_DataExtracted:
        CONF.VAR_DataExtracted[method_name] = {}
    if level_one not in CONF.VAR_DataExtracted[method_name]:
        # Execute action here
        if len(arguments) == 0:
            result = metho_to_execute()
        elif len(arguments) == 1:
            result = metho_to_execute(arguments[0])
        elif len(arguments) == 2:
            result = metho_to_execute(arguments[0], arguments[1])
        elif len(arguments) == 3:
            result = metho_to_execute(arguments[0], arguments[1], arguments[2])
        else:
            raise NotImplementedError(f'Argument handling for "{len(arguments)}" arguments is not implemented!')
        CONF.VAR_DataExtracted[method_name][level_one] = result
    else:
        print('Result found from previous execution, using stored data!')
        result = CONF.VAR_DataExtracted[method_name][level_one]
    return result
