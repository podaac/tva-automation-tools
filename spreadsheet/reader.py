'''Reader Module for Google Spreadsheet.'''
from gspread.cell import Cell
from gspread.worksheet import Worksheet

from spreadsheet.gsheet_base import GSheetBase


class Reader(GSheetBase):
    '''Class for methods to read Google Spreadsheets'''

    def CheckIfSheetExists(self, sheet_name: str) -> bool:
        '''Function for checking if the worksheet exists or not'''

        worksheets: list[Worksheet] = self.workbook.worksheets()
        do_exists = False
        for worksheet in worksheets:
            if worksheet.title == sheet_name:
                do_exists = True
                break
        print(f'\r\nChecking if sheet "{sheet_name}" exists: {do_exists}...')
        return do_exists


    def GetAllCellDataFromSheet(self, sheet_name: str):
        '''Function for reading aall cell data from the worksheet, except empty ones'''

        print(f'Reading cell information in sheet "{sheet_name}"...')
        worksheet = self.workbook.worksheet(sheet_name)
        cell_data_list: list[Cell] = worksheet.get_all_cells()
        result = {}
        for cell_data in cell_data_list:
            column_index = cell_data.col
            row_index = cell_data.row
            value = cell_data.value
            if value != '':
                if column_index not in result:
                    result[column_index] = {}
                if row_index not in result[column_index]:
                    result[column_index][row_index] = ''
                result[column_index][row_index] = value
        return result


    def GetColumnDataFromSheet(self, sheet_name: str, column_index: int) -> list[str]:
        '''Function for reading a single column data from the worksheet'''

        print(f'\r\nReading column "{column_index}" information in sheet "{sheet_name}"...')
        result = []
        worksheet = self.workbook.worksheet(sheet_name)

        result = worksheet.col_values(column_index)
        return result


    def GetSheetId(self, sheet_name: str) -> str:
        '''Function for getting the "gid" of the worksheet'''

        worksheet = self.workbook.worksheet(sheet_name)
        return worksheet.id
