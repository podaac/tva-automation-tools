'''Writer/Updater Module for Google Spreadsheet.'''
from gspread.cell import Cell
from gspread.utils import ValueInputOption

from spreadsheet.gsheet_base import GSheetBase


class Updater(GSheetBase):
    '''Class for methods to write/update Google Spreadsheets'''

    def CreateSheet(
        self,
        sheetName: str,
        rowCount: int = 50,
        columnCount: int = 10
    ):
        '''Function for creating a worksheet'''

        print(f'\r\nCreating new sheet "{sheetName}"...')
        self.workbook.add_worksheet(title=sheetName, rows=rowCount, cols=columnCount)


    def UpdateSheet(self, sheetName: str, data: dict):
        '''Function for updating a worksheet'''

        print(f'Updating sheet "{sheetName}" with new data...')
        worksheet = self.workbook.worksheet(sheetName)
        cell_list = []
        last_column_index = 0
        for column_index in data:
            last_column_index = max(last_column_index, column_index)
            for row_index in data[column_index]:
                value = data[column_index][row_index]
                cell_list.append(Cell(
                    row=row_index,
                    col=column_index,
                    value=value))
        worksheet.update_cells(cell_list, value_input_option=ValueInputOption.user_entered)


    def ClearSheet(self, sheetName: str, startRowIndex: int, endRowIndex: int, columnCountIndex: int):
        '''Function for clearing a worksheet'''

        print(f'Clearing sheet "{sheetName}" between rows "{startRowIndex}" and "{endRowIndex}"...')
        worksheet = self.workbook.worksheet(sheetName)
        cell_list = []
        for column_index in range(1, columnCountIndex, 1):
            for row_index in range(startRowIndex, endRowIndex, 1):
                cell_list.append(Cell(
                    row=row_index,
                    col=column_index,
                    value=''))
        worksheet.update_cells(cell_list, value_input_option=ValueInputOption.user_entered)


    def SetCellHorizontalAlignment(
        self,
        sheetName: str,
        cellCoordinate: str,
        alignment: str = 'CENTER'
    ):
        '''Function for setting cell horizontal alignment'''

        print(f'Updating sheet "{sheetName}" cell "{cellCoordinate}" horizontal alignment to "{alignment}"...')
        worksheet = self.workbook.worksheet(sheetName)
        worksheet.format(cellCoordinate, {'horizontalAlignment': alignment})
