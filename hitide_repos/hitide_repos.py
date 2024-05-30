from datetime import datetime
import pytz

import gspread

def main(args=None):

    gc = gspread.service_account()
    SPREADSHEET_ID = '1wBIbd56mBDYQLKwHtK1Dzk7n6mtHMc9kftiRTQ63NOw'

    workbook = gc.open_by_key(SPREADSHEET_ID)

    worksheet = workbook.worksheet("Sheet1")

    all_rows = worksheet.get_all_values()

    print(all_rows)

    now = datetime.now(pytz.timezone('US/Pacific'))
    current_month = now.strftime("%Y-%m")

    worksheet.update([[current_month]], "C8")

if __name__ == "__main__":
    main()
