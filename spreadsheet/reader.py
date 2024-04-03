from spreadsheet.gsheetbase import GSheetBase


class Reader(GSheetBase):
    
    def GetDataFromSheet(self, sheetName:str):
        worksheet = self.workbook.worksheet(sheetName)
        data = worksheet.get_all_records()
        print(f'all record type: {type(data)}')
        print(f'all record data: {data}')
        
        data2 = worksheet.get_all_cells()
        print(f'all cells type: {type(data2)}')
        print(f'all cells data: {data2}')
        
        data3 = worksheet.col_values(1)
        print(f'col_values type: {type(data3)}')
        print(f'col_values data: {data3}')
        return data
    
        
    def GetColumnDataFromSheet(self, sheetName:str, columnName:str) -> list[str]:
        columnData = []
        worksheet = self.workbook.worksheet(sheetName)
        
        worksheet.get_values()
        return columnData