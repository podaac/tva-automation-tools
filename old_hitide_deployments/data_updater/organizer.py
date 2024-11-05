'''Main module of the Repo Status Updater'''
# pylint: disable=E1101, R0903
# E1101 => dynamic method usage
# R0903 => Need only 1 public method

from datetime import datetime
from copy import deepcopy
from time import sleep

import re
import pytz

from data_updater.distributor import Distributor
from spreadsheet import Interactor
import config.config


# Constants
SPREADSHEET_ID = '1wBIbd56mBDYQLKwHtK1Dzk7n6mtHMc9kftiRTQ63NOw'
REPOS_SHEETNAME = 'Repos'
REPOS_COLUMN_INDEX_REPOS = 1
REPOS_COLUMN_INDEX_SHEET_LINK = 2
REPOS_COLUMN_INDEX_LAST_UPDATE_TIME = 3
REPOS_COLUMN_INDEX_GITHUB_ADDRESS = 4
IGNORE_REPO_LIST = ['Repo', 'Repository']
REPO_TEMPLATE_SHEETNAME = 'Repo Template'
TEMPLATE_COLUMN_INDEX_VALUE = 3
TEMPLATE_COLUMN_INDEX_METHOD = 4
TEMPLATE_COLUMN_INDEX_ARGS = 5
TEMPLATE_ROW_INDEX_HEADER = 5
CONF = config.config.Config


class Organizer():
    '''Class to organize the required updates'''

    def Start():
        '''Function to organize the required updates
            Main function of the repository'''

        spreadsheet = Interactor(SPREADSHEET_ID)
        repo_template = GetRepoTemplate(spreadsheet)
        repo_template[6] = {}

        repo_data_original = spreadsheet.reader.GetAllCellDataFromSheet(REPOS_SHEETNAME)
        repo_data = deepcopy(repo_data_original)

        # Update each repository one by one
        for row_index_repo in repo_data[REPOS_COLUMN_INDEX_REPOS]:
            CONF.VAR_DataExtracted = {}
            repo_name = repo_data[REPOS_COLUMN_INDEX_REPOS][row_index_repo]

            print('\r\n\r\n\r\n=============================================================================================================')
            print(f'============================== Starting extraction for "{repo_name}" ==============================')
            print(f'Place on Repo page: {row_index_repo}')
            if repo_name in IGNORE_REPO_LIST:
                continue

            # Stop after the first line, this is for code testing and debug
            # if row_index_repo > 3:
            #     print('Stopping run...')
            #     break

            repo_link = ''
            if row_index_repo in repo_data[REPOS_COLUMN_INDEX_GITHUB_ADDRESS]:
                repo_link = repo_data[REPOS_COLUMN_INDEX_GITHUB_ADDRESS][row_index_repo]

            # Create the sheet
            use_template_data = False        # Force update all sheets from the Template data
            sheet_name = GetOrGenerateSheetName(
                spreadsheet=spreadsheet,
                row_index=row_index_repo,
                data=repo_data,
                template=repo_template,
                force_update=use_template_data
            )

            data_of_sheet_original = spreadsheet.reader.GetAllCellDataFromSheet(sheet_name)
            data_of_sheet = deepcopy(data_of_sheet_original)

            # Update the values using the method listed in the Method to Use column
            for row_index_template in data_of_sheet[1]:
                if row_index_template > TEMPLATE_ROW_INDEX_HEADER:
                    if row_index_template in data_of_sheet[TEMPLATE_COLUMN_INDEX_METHOD]:
                        method_name = data_of_sheet[TEMPLATE_COLUMN_INDEX_METHOD][row_index_template]
                    else:
                        method_name = None

                    args = []
                    if row_index_template in data_of_sheet[TEMPLATE_COLUMN_INDEX_ARGS]:
                        args = ExtractArguments(
                            field_content=data_of_sheet[TEMPLATE_COLUMN_INDEX_ARGS][row_index_template],
                            repo_link=repo_link,
                            arguments_to_replace=['repo_link'])
                    data = GetData(
                        method_name=method_name,
                        arguments=args)
                    data_of_sheet[TEMPLATE_COLUMN_INDEX_VALUE][row_index_template] = data

            if data_of_sheet_original != data_of_sheet:
                print(f'\r\n\r\n================================ Data for "{sheet_name}" sheet ================================')
                print(f'{data_of_sheet}\r\n\r\n')
                spreadsheet.updater.UpdateSheet(sheet_name, data_of_sheet)
                # Added 20 seconds sleep after every sheet to avoid user/minute quota reach
                sleep(20)

            # Update the Last Updated field in the Repos sheet
            now = datetime.now(pytz.timezone('US/Pacific'))
            repo_data[REPOS_COLUMN_INDEX_LAST_UPDATE_TIME][row_index_repo] = now.strftime(CONF.TimeFormat)
        if repo_data_original != repo_data:
            print(f'\r\n\r\n================================ Data for "{REPOS_SHEETNAME}" sheet ================================')
            print(f'{repo_data}\r\n\r\n')
            spreadsheet.updater.UpdateSheet(REPOS_SHEETNAME, repo_data)


def GetRepoTemplate(spreadsheet) -> dict:
    '''Function to get the repo template data'''

    repo_template = spreadsheet.reader.GetAllCellDataFromSheet(REPO_TEMPLATE_SHEETNAME)
    template_row_index_header = TEMPLATE_ROW_INDEX_HEADER
    for row_index in repo_template[TEMPLATE_COLUMN_INDEX_VALUE]:
        if repo_template[TEMPLATE_COLUMN_INDEX_VALUE] == 'Value':
            template_row_index_header = row_index

    # Empty Value and Source data from template sheet
    value_header = repo_template[TEMPLATE_COLUMN_INDEX_VALUE][template_row_index_header]
    repo_template[TEMPLATE_COLUMN_INDEX_VALUE] = {}
    repo_template[TEMPLATE_COLUMN_INDEX_VALUE][template_row_index_header] = value_header
    return repo_template


def ExtractArguments(field_content: str, repo_link: str, arguments_to_replace: list) -> list:
    '''Function to get to convert the arguments from the prived string into the correct types'''

    result = []
    temp_results = field_content.split(';')
    for temp_result in temp_results:
        temp: str = temp_result
        temp = temp.strip(' ')
        if temp.startswith('['):
            stripped_values = []
            values = temp[1:-1].split(',')
            for value in values:
                stripped_values.append(value.strip(' '))
            result.append(stripped_values)
        elif temp.startswith('{'):
            value = dict(temp)
            result.append(value)
        else:
            if temp.lower() in arguments_to_replace:
                result.append(repo_link)
            else:
                result.append(temp)
    return result


def GetData(method_name: str, arguments: list) -> str:
    '''Function to get execute the named method with the arguments'''

    data = 'Location information is missing!'
    print(f'\r\n====================== Start of method "{method_name}" ======================')
    print(f'Arguments to use: {arguments}\r\n')
    if method_name != '' and method_name is not None:
        method_to_execute = getattr(Distributor, method_name)
        if len(arguments) == 0:
            data = method_to_execute()
        elif len(arguments) == 1:
            data = method_to_execute(arguments[0])
        elif len(arguments) == 2:
            data = method_to_execute(arguments[0], arguments[1])
        elif len(arguments) == 3:
            data = method_to_execute(arguments[0], arguments[1], arguments[2])
    print(f'\r\nInformation found: "{data}"')

    return data


def GetOrGenerateSheetName(spreadsheet: Interactor, row_index: int, data: dict, template: dict, force_update: bool = False) -> str:
    '''Function to get execute the named method with the arguments'''

    repo_name = data[REPOS_COLUMN_INDEX_REPOS][row_index]
    if row_index in data[REPOS_COLUMN_INDEX_SHEET_LINK]:
        hyperlink = data[REPOS_COLUMN_INDEX_SHEET_LINK][row_index]
        print(f'\r\nCell content: {hyperlink}')
        print(f'Is hyperlink: {hyperlink.startswith("=")}')
        if hyperlink.startswith('='):
            pattern = r"=HYPERLINK\(\"#gid=(.*)\",\"(.*)\"\)"
            mo = re.findall(pattern, hyperlink)
            for i in range(0, len(mo), 1):
                print(f'mo[{i}[]: {mo[i]}')
            sheet_name = mo[3]
        else:
            sheet_name = hyperlink
    else:
        sheet_name = repo_name

    print(f'Sheet name: {sheet_name}')
    for i in range(0, row_index + 1, 1):
        if i in data[REPOS_COLUMN_INDEX_SHEET_LINK]:
            prev_sheet_name = data[REPOS_COLUMN_INDEX_SHEET_LINK][i]
            if prev_sheet_name == sheet_name and i != row_index:
                sheet_name = f'{sheet_name}_({i})'
                print(f'Renamed sheet to "{sheet_name}"')

    do_exists = spreadsheet.reader.CheckIfSheetExists(sheet_name)
    # Update the sheets with data from the template
    if not do_exists or force_update:
        row_count = 50
        column_count = 10
        updated_template = deepcopy(template)
        updated_template[2][2] = repo_name
        updated_template[2][3] = data[REPOS_COLUMN_INDEX_GITHUB_ADDRESS][row_index]
        # Create the sheet or force clear the existing one for the update
        if not force_update:
            spreadsheet.updater.CreateSheet(
                sheet_name=sheet_name,
                row_count=row_count,
                column_count=column_count)
        else:
            spreadsheet.updater.ClearSheet(sheet_name, TEMPLATE_ROW_INDEX_HEADER + 1, row_count, column_count)
        spreadsheet.updater.UpdateSheet(sheet_name, updated_template)
    # Create the hyperlink in the Repos sheet to the new sheet
    gid = spreadsheet.reader.GetSheetId(sheet_name)
    data[REPOS_COLUMN_INDEX_SHEET_LINK][row_index] = f'=HYPERLINK("#gid={gid}","{sheet_name}")'

    return sheet_name
