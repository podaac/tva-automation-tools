from datetime import datetime

from spreadsheet import Interactor

import pytz

def main(args=None):

    SPREADSHEET_ID = '1wBIbd56mBDYQLKwHtK1Dzk7n6mtHMc9kftiRTQ63NOw'
    hitide_sheet = Interactor(SPREADSHEET_ID)
    
    reposSheetName = 'repos'
    repoListColumnName = 'A'
    repoList = hitide_sheet.Reader.GetDataFromSheet(reposSheetName)
    originalDataOfSheet = hitide_sheet.Reader.GetDataFromSheet('TestDev')
    updatedData = originalDataOfSheet
    hitide_sheet.Updater.UpdateSheet('TestDev', updatedData)

    # worksheet = workbook.worksheet("Sheet1")

    # all_rows = worksheet.get_all_values()

    print(f'repoList\r\n{repoList}\r\n\r\n')
    print(f'originalDataOfSheet:\r\n{originalDataOfSheet}')

    now = datetime.now(pytz.timezone('US/Pacific'))
    current_month = now.strftime("%Y-%m")

    # worksheet.update([[current_month]], "C8")

if __name__ == "__main__":
    main()
