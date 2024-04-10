"""Main module of the Repo Status Updater"""
# pylint: disable=E1101, R0903
# E1101 => dynamic method usage
# R0903 => only one main class

from datetime import datetime
from copy import deepcopy
from time import sleep

import pytz

from data_updater.distributor import Distributor
from spreadsheet import Interactor
import config.config


# File wide variables
SPREADSHEET_ID = '1wBIbd56mBDYQLKwHtK1Dzk7n6mtHMc9kftiRTQ63NOw'
REPOS_SHEETNAME = 'Repos'
REPOS_COLUMN_INDEX_REPOS = 1
REPOS_COLUMN_INDEX_SHEET_LINK = 2
REPOS_COLUMN_INDEX_LAST_UPDATE_TIME = 3
REPOS_COLUMN_INDEX_GIT_ADDRESS = 4
IGNORE_REPO_LIST = ['Repo', 'Repository']
REPO_TEMPLATE_SHEETNAME = 'Repo Template'
TEMPLATE_COLUMN_INDEX_VALUE = 3
TEMPLATE_COLUMN_INDEX_METHOD = 4
TEMPLATE_COLUMN_INDEX_ARGS = 5
TEMPLATE_ROW_INDEX_HEADER = 5
CONF = config.config.Config

class Organizer():
    """Class to organize the required updates"""

    def Start():
        """Function to organize the required updates
            Main function of the repository"""

        spreadsheet = Interactor(SPREADSHEET_ID)
        repo_template = GetRepoTemplate(spreadsheet)
        repo_template[6] = {}

        repo_data_original = spreadsheet.reader.GetAllCellDataFromSheet(REPOS_SHEETNAME)
        repo_data = deepcopy(repo_data_original)

        # Update each repository one by one
        for row_index_repo in repo_data[REPOS_COLUMN_INDEX_REPOS]:
            repo_name = repo_data[REPOS_COLUMN_INDEX_REPOS][row_index_repo]
            if repo_name in IGNORE_REPO_LIST:
                continue

            repo_link = ""
            if row_index_repo in repo_data[REPOS_COLUMN_INDEX_GIT_ADDRESS]:
                repo_link = repo_data[REPOS_COLUMN_INDEX_GIT_ADDRESS][row_index_repo]

            # sheet_name = repo_name
            sheet_name = GetOrGenerateSheetName(
                            spreadsheet = spreadsheet,
                            rowIndex = row_index_repo,
                            data = repo_data,
                            template = repo_template)

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
                            fieldContent = data_of_sheet[TEMPLATE_COLUMN_INDEX_ARGS][row_index_template],
                            repoLink = repo_link,
                            argumentsToReplace = ['repo_link'])
                    data = GetData(
                        methodName = method_name,
                        arguments = args)
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
    """Function to get the repo template data"""

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


def ExtractArguments(fieldContent:str, repoLink:str, argumentsToReplace:list) -> list:
    """Function to get to convert the arguments from the prived string into the correct types"""

    result = []
    temp_results = fieldContent.split(';')
    for temp_result in temp_results:
        temp:str = temp_result
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
            if temp.lower() in argumentsToReplace:
                result.append(repoLink)
            else:
                result.append(temp)
    return result


def GetData(methodName:str, arguments:list) -> str:
    """Function to get execute the named method with the arguments"""

    data = "Location information is missing!"
    if methodName != "" and methodName is not None:
        method_to_execute = getattr(Distributor, methodName)
        print(f'\r\n====================== Start of method "{methodName}" ======================')
        print(f'Arguments to use: {arguments}\r\n')
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


def GetOrGenerateSheetName(spreadsheet:Interactor, rowIndex:int, data:dict, template:dict) -> str:
    """Function to get execute the named method with the arguments"""

    repo_name = data[REPOS_COLUMN_INDEX_REPOS][rowIndex]
    if rowIndex in data[REPOS_COLUMN_INDEX_SHEET_LINK]:
        sheet_name = data[REPOS_COLUMN_INDEX_SHEET_LINK][rowIndex]
    else:
        sheet_name = repo_name

    for i in range(0, rowIndex + 1, 1):
        if i in data[REPOS_COLUMN_INDEX_SHEET_LINK]:
            prev_sheet_name = data[REPOS_COLUMN_INDEX_SHEET_LINK][i]
            print(f'rowIndex: {rowIndex}')
            print(f'i: {i}')
            print(f'prev_sheet_name: {prev_sheet_name}')
            if prev_sheet_name == sheet_name and i != rowIndex:
                sheet_name = f'{sheet_name}_({i})'
                print(f'Renamed sheet to "{sheet_name}"')

    do_exists = spreadsheet.reader.CheckIfSheetExists(sheet_name)
    if not do_exists:
        # Create the sheet and the corresponding hyperlink
        updated_template = deepcopy(template)
        updated_template[2][2] = repo_name
        updated_template[2][3] = data[REPOS_COLUMN_INDEX_GIT_ADDRESS][rowIndex]
        spreadsheet.updater.CreateSheet(
            sheetName = sheet_name,
            rowCount = 50,
            columnCount = 10)
        spreadsheet.updater.UpdateSheet(sheet_name, updated_template)
        gid = spreadsheet.reader.GetSheetId(sheet_name)
        data[REPOS_COLUMN_INDEX_SHEET_LINK][rowIndex] = f'=HYPERLINK("#gid={gid}","{sheet_name}")'

    return sheet_name
