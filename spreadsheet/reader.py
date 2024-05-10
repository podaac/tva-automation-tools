'''Reader Module for Google Spreadsheet.'''
from gspread.cell import Cell
from gspread.worksheet import Worksheet

from spreadsheet.gsheet_base import GSheetBase


class Reader(GSheetBase):
    '''Class for methods to read Google Spreadsheets'''

    def CheckIfSheetExists(self, sheetName: str) -> bool:
        '''Function for checking if the worksheet exists or not'''

        worksheets: list[Worksheet] = self.workbook.worksheets()
        do_exists = False
        for worksheet in worksheets:
            if worksheet.title == sheetName:
                do_exists = True
                break
        print(f'\r\nChecking if sheet "{sheetName}" exists: {do_exists}...')
        return do_exists


    def GetAllCellDataFromSheet(self, sheetName: str):
        '''Function for reading aall cell data from the worksheet, except empty ones'''

        print(f'Reading cell information in sheet "{sheetName}"...')
        worksheet = self.workbook.worksheet(sheetName)
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


    def GetColumnDataFromSheet(self, sheetName: str, columnIndex: int) -> list[str]:
        '''Function for reading a single column data from the worksheet'''

        print(f'\r\nReading column "{columnIndex}" information in sheet "{sheetName}"...')
        result = []
        worksheet = self.workbook.worksheet(sheetName)

        result = worksheet.col_values(columnIndex)
        return result


    def GetSheetId(self, sheetName: str) -> str:
        '''Function for getting the "gid" of the worksheet'''

        worksheet = self.workbook.worksheet(sheetName)
        return worksheet.id
