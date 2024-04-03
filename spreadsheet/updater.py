from spreadsheet.gsheetbase import GSheetBase


class Updater(GSheetBase):
    
    def CreateSheet(self, sheetName:str, rowCount:int=50, columnCount:int=10):
        self.workbook.add_worksheet(title = sheetName, rows = rowCount, cols = columnCount)
    
    
    def UpdateSheet(self, sheetName:str, data:dict):
        worksheet = self.workbook.worksheet(sheetName)
        for columnIndex in data.keys():
            for rowIndex in data[columnIndex].keys():
                value = data[columnIndex][rowIndex]
                worksheet.update_cell(
                    col = columnIndex,
                    row = rowIndex,
                    value = value)
        worksheet.update