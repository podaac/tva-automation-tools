from spreadsheet.gsheetbase import GSheetBase

from gspread.cell import Cell


class Reader(GSheetBase):
    
    def GetAllCellDataFromSheet(self, sheetName:str):
        worksheet = self.workbook.worksheet(sheetName)
        cellDataList:list[Cell] = worksheet.get_all_cells()
        
        result = {}
        for cellData in cellDataList:
            columnIndex = cellData.col
            rowIndex = cellData.row
            value = cellData.value
            if value != "":
                if columnIndex not in result.keys():
                    result[columnIndex] = {}
                if rowIndex not in result[columnIndex].keys():
                    result[columnIndex][rowIndex] = ''
                result[columnIndex][rowIndex] = value
        return result
    
        
    def GetColumnDataFromSheet(self, sheetName:str, columnIndex:int) -> list[str]:
        columnData = []
        worksheet = self.workbook.worksheet(sheetName)
        
        columnData = worksheet.col_values(columnIndex)
        return columnData