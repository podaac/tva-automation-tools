"""Writer/Updater Module for Google Spreadsheet."""
from gspread.cell import Cell

from spreadsheet.gsheet_base import GSheetBase


class Updater(GSheetBase):
    """Class for methods to write/update Google Spreadsheets"""

    def CreateSheet(self, sheetName:str, rowCount:int=50, columnCount:int=10):
        """Function for creating a worksheet"""

        print(f'\r\nCreating new sheet "{sheetName}"...')
        self.workbook.add_worksheet(title = sheetName, rows = rowCount, cols = columnCount)


    def UpdateSheet(self, sheetName:str, data:dict):
        """Function for updating a worksheet"""

        print(f'Updating sheet "{sheetName}" with new data...')
        worksheet = self.workbook.worksheet(sheetName)
        cell_list = []
        for column_index in data:
            for row_index in data[column_index]:
                value = data[column_index][row_index]
                cell_list.append(Cell(
                    row = row_index,
                    col = column_index,
                    value = value))
        worksheet.update_cells(cell_list)
