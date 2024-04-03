from spreadsheet.gsheetbase import GSheetBase


class Updater(GSheetBase):
    
    def CreateSheet(self, sheetName:str):
        self.workbook.add_worksheet(title = sheetName, rows = 30, cols = 10)
    
    
    def UpdateSheet(self, sheetName:str, data:dict):
        worksheet = self.workbook.worksheet(sheetName)
        for column in data.keys():
            for row in data[column].keys():
                value = data[column][row]
                worksheet.update_cell(
                    col = column,
                    row = row,
                    value = value)
        worksheet.update