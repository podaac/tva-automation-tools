import os
import pytz
from datetime import datetime
import gspread
import logging
import sys

from retrying import retry


gc = gspread.service_account()

spreadsheet_id = os.environ['SPREADSHEET_ID']

workbook = gc.open_by_key(spreadsheet_id)


# Define a custom exception for retries
class RetryError(Exception):
    pass

# Retry decorator to handle exceptions and implement backoff
@retry(wait_exponential_multiplier=1000, wait_exponential_max=30000, stop_max_attempt_number=7, retry_on_exception=lambda ex: isinstance(ex, RetryError))
def update_sheet(worksheet, data, cell):
    try:
         
        # Update the data in the worksheet
        worksheet.update(data, cell)  # Update cell A1 with your data
        
    except gspread.exceptions.GSpreadException as e:
        print(f"Error: {e}")
        raise RetryError(f"Failed to update. Retrying...")


def get_regression_sheet_table():

    collections_ws = workbook.worksheet("Regression Tests")
    collection_table = collections_ws.get_all_values()

    return collection_table


def create_logger():
    """Return configured logger from parsed cli args."""

    log_file = "post_regression_results_log.txt"
    logging.basicConfig(filename=log_file)
    logger = logging.getLogger("regression_tests")
    logger.setLevel(getattr(logging, "DEBUG"))
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def main(args=None):
 
    logger = create_logger()

    logger.info(f"Started post regression results: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    collection_table = get_regression_sheet_table()

    for row in collection_table[1:]:
        print(row)

    logger.info(f"Finished all collections: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")


if __name__ == "__main__":
    main()
