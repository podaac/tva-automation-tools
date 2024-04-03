from spreadsheet.reader import Reader
from spreadsheet.updater import Updater


class Interactor():
    
    def __init__(self, spreadsheetID: str) -> None:
        self._reader = Reader(spreadsheetID)
        self._updater = Updater(spreadsheetID)

    @property 
    def Reader(self):
        return self._reader
    
    @property 
    def Updater(self):
        return self._updater
        