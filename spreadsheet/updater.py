'''Writer/Updater Module for Google Spreadsheet.'''
from gspread.cell import Cell
from gspread.utils import ValueInputOption

from spreadsheet.gsheet_base import GSheetBase


class Updater(GSheetBase):
    '''Class for methods to write/update Google Spreadsheets'''

    def CreateSheet(
        self,
        sheet_name: str,
        row_count: int = 50,
        column_count: int = 10
    ):
        '''Function for creating a worksheet'''

        print(f'\r\nCreating new sheet "{sheet_name}"...')
        self.workbook.add_worksheet(title=sheet_name, rows=row_count, cols=column_count)


    def UpdateSheet(self, sheet_name: str, data: dict):
        '''Function for updating a worksheet'''

        print(f'Updating sheet "{sheet_name}" with new data...')
        worksheet = self.workbook.worksheet(sheet_name)
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


    def ClearSheet(self, sheet_name: str, start_row_index: int, end_row_index: int, column_count_index: int):
        '''Function for clearing a worksheet'''

        print(f'Clearing sheet "{sheet_name}" between rows "{start_row_index}" and "{end_row_index}"...')
        worksheet = self.workbook.worksheet(sheet_name)
        cell_list = []
        for column_index in range(1, column_count_index, 1):
            for row_index in range(start_row_index, end_row_index, 1):
                cell_list.append(Cell(
                    row=row_index,
                    col=column_index,
                    value=''))
        worksheet.update_cells(cell_list, value_input_option=ValueInputOption.user_entered)


    def SetCellHorizontalAlignment(
        self,
        sheet_name: str,
        cell_coordinate: str,
        alignment: str = 'CENTER'
    ):
        '''Function for setting cell horizontal alignment'''

        print(f'Updating sheet "{sheet_name}" cell "{cell_coordinate}" horizontal alignment to "{alignment}"...')
        worksheet = self.workbook.worksheet(sheet_name)
        worksheet.format(cell_coordinate, {'horizontalAlignment': alignment})
