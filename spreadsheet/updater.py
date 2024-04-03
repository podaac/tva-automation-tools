"""Writer/Updater Module for Google Spreadsheet."""
from spreadsheet.gsheet_base import GSheetBase


class Updater(GSheetBase):
    """Class for methods to write/update Google Spreadsheets"""

    def CreateSheet(self, sheetName:str, rowCount:int=50, columnCount:int=10):
        """Function for creating a worksheet"""

        self.workbook.add_worksheet(title = sheetName, rows = rowCount, cols = columnCount)


    def UpdateSheet(self, sheetName:str, data:dict):
        """Function for updating a worksheet"""

        worksheet = self.workbook.worksheet(sheetName)
        for column_index in data:
            for row_index in data[column_index]:
                value = data[column_index][row_index]
                worksheet.update_cell(
                    col = column_index,
                    row = row_index,
                    value = value)
