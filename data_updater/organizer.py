"""Main module of the Repo Status Updater"""
from datetime import datetime

import pytz

from spreadsheet import Interactor



# File wide variables
SPREADSHEET_ID = '1wBIbd56mBDYQLKwHtK1Dzk7n6mtHMc9kftiRTQ63NOw'
REPOS_SHEETNAME = 'Repos'
class Organizer():
    """Class to organize the required updates"""

    def Main(args):
        """Function to organize the required updates
            Main function of the repository"""

        spreadsheet = Interactor(SPREADSHEET_ID)

        column_index_repos = 1
        column_index_links = 2
        column_index_updated = 3
        repo_list = spreadsheet.reader.GetColumnDataFromSheet(REPOS_SHEETNAME, column_index_repos).remove('Repos')
        for repo_name in repo_list:
            do_exists = spreadsheet.reader.CheckIfSheetExists(repo_name)
            if not do_exists:
                pass
                # spreadsheet.Updater.CreateSheet(
                #     sheetName = repo_name,
                #     rowCount = 50,
                #     columnCount = 10)
        original_data_of_sheet = spreadsheet.reader.GetAllCellDataFromSheet('TestDev')
        # updated_data = original_data_of_sheet

        print(f'\r\nrepoList\r\n{repo_list}\r\n\r\n')
        print(f'originalDataOfSheet:\r\n{original_data_of_sheet}')

        now = datetime.now(pytz.timezone('US/Pacific'))
        # current_month = now.strftime("%Y-%m")

        # spreadsheet.Updater.UpdateSheet(REPOS_SHEETNAME, data)
