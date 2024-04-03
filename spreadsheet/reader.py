from spreadsheet.gsheetbase import GSheetBase


class Reader(GSheetBase):
    
    def GetDataFromSheet(self, sheetName:str):
        worksheet = self.workbook.worksheet(sheetName)
        data = worksheet.get_all_values()
        print(f'type: {type(data)}')
        print(f'data: {data}')
        return data
    
        
    def GetColumnDataFromSheet(self, sheetName:str, columnName:str) -> list[str]:
        columnData = []
        worksheet = self.workbook.worksheet(sheetName)
        
        worksheet.get_values()
        return columnData