"""Reader Module for Google Spreadsheet."""
from gspread.cell import Cell

from spreadsheet.gsheet_base import GSheetBase


class Reader(GSheetBase):
    """Class for methods to read Google Spreadsheets"""

    def GetAllCellDataFromSheet(self, sheetName:str):
        """Function for reading aall cell data from the worksheet, except empty ones"""

        worksheet = self.workbook.worksheet(sheetName)
        cell_data_list:list[Cell] = worksheet.get_all_cells()

        result = {}
        for cell_data in cell_data_list:
            column_index = cell_data.col
            row_index = cell_data.row
            value = cell_data.value
            if value != "":
                if column_index not in result:
                    result[column_index] = {}
                if row_index not in result[column_index]:
                    result[column_index][row_index] = ''
                result[column_index][row_index] = value
        return result


    def GetColumnDataFromSheet(self, sheetName:str, columnIndex:int) -> list[str]:
        """Function for reading a single column data from the worksheet"""

        result = []
        worksheet = self.workbook.worksheet(sheetName)

        result = worksheet.col_values(columnIndex)
        return result
