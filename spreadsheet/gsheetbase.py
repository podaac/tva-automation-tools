
import gspread


class GSheetBase():
    def __init__(self, spreadsheetID:str) -> None:
        self._service = gspread.service_account()
        self._workbook = self.service.open_by_key(spreadsheetID)

    @property 
    def service(self):
        return self._service
    
    @property 
    def workbook(self):
        return self._workbook
        