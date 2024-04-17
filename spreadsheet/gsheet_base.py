"""Base Module for Google Spreadsheet related classes."""
import gspread


class GSheetBase():
    """Base Class for Google Spreadsheet"""

    def __init__(self, spreadsheetID:str) -> None:
        """Function for class initialization"""

        self._service = gspread.service_account()
        self._workbook = self.service.open_by_key(spreadsheetID)

    @property
    def service(self):
        """Service property"""
        return self._service

    @property
    def workbook(self):
        """Workbook property"""
        return self._workbook
