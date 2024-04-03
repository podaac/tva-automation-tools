from datetime import datetime

from spreadsheet import Interactor

import pytz


class Organizer():

    def Main():
        SPREADSHEET_ID = '1wBIbd56mBDYQLKwHtK1Dzk7n6mtHMc9kftiRTQ63NOw'
        hitide_sheet = Interactor(SPREADSHEET_ID)

        reposSheetName = 'Repos'
        repoListColumnName = 'A'
        repoList = hitide_sheet.Reader.GetColumnDataFromSheet(reposSheetName, 1)
        originalDataOfSheet = hitide_sheet.Reader.GetAllCellDataFromSheet('TestDev')
        updatedData = originalDataOfSheet

        print(f'\r\nrepoList\r\n{repoList}\r\n\r\n')
        print(f'originalDataOfSheet:\r\n{originalDataOfSheet}')

        now = datetime.now(pytz.timezone('US/Pacific'))
        current_month = now.strftime("%Y-%m")

        # worksheet.update([[current_month]], "C8")
