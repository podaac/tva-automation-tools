'''Module to organize and initiate reader and updater methods for Google Spreadsheet.'''
from spreadsheet.reader import Reader
from spreadsheet.updater import Updater


class Interactor():
    '''Collection Class to interact with Google Spreadsheet'''

    def __init__(self, spreadsheet_id: str) -> None:
        '''Function for class initialization'''

        self._reader = Reader(spreadsheet_id)
        self._updater = Updater(spreadsheet_id)


    @property
    def reader(self):
        '''Reader property'''
        return self._reader


    @property
    def updater(self):
        '''Updater property'''
        return self._updater
