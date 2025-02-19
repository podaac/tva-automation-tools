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


def check_tool_pass_fail(workdir: str, short_name: str, granule_id: str, tool: str, output_dir_name: str) -> str:
    """
    Check if a tool's processing passed or failed for a specific granule.
    
    Args:
        workdir (str): The base working directory path
        short_name (str): The collection identifier
        granule_id (str): The granule identifier
        tool (str): The tool name (e.g. 'forge', 'tig', 'forge-py')
        output_dir_name (str): Name of output directory to check
    
    Returns:
        str: 'PASS' if successful, 'FAIL' if failed, 'SKIP' if skipped, or 'N/A' if no results found
    """
    # Construct path to granule directory
    collection_dir = os.path.join(workdir, short_name)
    granule_dir = os.path.join(collection_dir, granule_id)
    output_dir = os.path.join(granule_dir, output_dir_name)
    
    # Convert forge-py to forge_py for filenames
    file_tool = tool.replace('-', '_')
    
    # Check for skip file
    skip_file = os.path.join(output_dir, f'{file_tool}_skip.txt')
    if os.path.exists(skip_file):
        return ''
        
    # Check for success file
    success_file = os.path.join(output_dir, f'{file_tool}_successful.txt')
    if os.path.exists(success_file):
        return 'PASS'
        
    # Check for failure file
    fail_file = os.path.join(output_dir, f'{file_tool}_failed.txt')
    if os.path.exists(fail_file):
        return 'FAIL'
        
    return ''


def get_all_image_counts(workdir: str, short_name: str, granule_id: str) -> dict:
    """
    Get image counts for all TIG output directories for a specific granule.
    
    Args:
        workdir (str): The base working directory path
        short_name (str): The collection identifier
        granule_id (str): The granule identifier
        
    Returns:
        dict: Dictionary mapping output directory names to their image counts
    """
    # Construct path to granule directory
    collection_dir = os.path.join(workdir, short_name)
    granule_dir = os.path.join(collection_dir, granule_id)
    
    # Initialize results dictionary
    image_counts = {}
    
    # Get all directories in granule dir that start with 'tig'
    for dirname in os.listdir(granule_dir):
        if dirname.startswith('tig'):
            output_dir = os.path.join(granule_dir, dirname)
            if os.path.isdir(output_dir):
                # Count .png files in this output directory
                png_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
                image_counts[dirname] = len(png_files)
                
    return image_counts


def get_image_count(workdir: str, short_name: str, granule_id: str) -> int:
    """
    Retrieve the image count for a specific granule given its collection short name and granule ID.
    
    Args:
        workdir (str): The base working directory path
        short_name (str): The collection identifier
        granule_id (str): The granule identifier
    
    Returns:
        int: The number of .png images found in the granule's output directory
    """
    # Construct path to granule directory
    collection_dir = os.path.join(workdir, short_name)
    granule_dir = os.path.join(collection_dir, granule_id)
    output_dir = os.path.join(granule_dir, 'output')
    
    # Check if output directory exists
    if not os.path.exists(output_dir):
        return 0
        
    # Count .png files in output directory
    png_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
    return len(png_files)


def process_granule(short_name: str, granule_id: str) -> dict:
    """
    Process a single granule based on its short name and granule ID.
    
    Args:
        short_name: Short name of the collection.
        granule_id: ID of the granule to process.
        
    Returns:
        dict: Dictionary containing the image count for this granule
    """
    logger = logging.getLogger("regression_tests")
    logger.info(f"Processing granule: {granule_id} from collection: {short_name}")
    
    # Get the image count for this granule
    image_counts = get_all_image_counts('workdir', short_name, granule_id)
    logger.info(f"Found {image_counts} images for granule {granule_id}")
    
    # Get Forge pass/fail status
    forge_status = check_tool_pass_fail('workdir', short_name, granule_id, 'forge', 'forge_0.12.0')
    logger.info(f"Forge status for granule {granule_id}: {forge_status}")

    # Get TIG pass/fail status
    tig_status = check_tool_pass_fail('workdir', short_name, granule_id, 'tig', 'tig_0.13.0')
    logger.info(f"TIG status for granule {granule_id}: {tig_status}")

    # Get forge-py pass/fail status
    forge_py_status = check_tool_pass_fail('workdir', short_name, granule_id, 'forge-py', 'forge_py_0.4.0')
    logger.info(f"Forge-py status for granule {granule_id}: {forge_py_status}")

    logger.info(f"Granule {granule_id} processed successfully.")
    
    return {
        'image_counts': image_counts,
        'forge_status': forge_status,
        'tig_status': tig_status,
        'forge_py_status': forge_py_status
    }


def insert_value_into_row(row: list, column_name: str, header_row: list, value: str) -> None:
    """
    Insert value into a specific column of a collection table row.
    
    Args:
        row (list): A single row from the collection table containing collection data
        column_name (str): Name of the column to insert value into
        header_row (list): The header row containing column names
        value (str): The value to insert into the specified column
    """
    logger = logging.getLogger("regression_tests")
    
    # Find the column index
    col_index = None
    for i, header in enumerate(header_row):
        if header == column_name:
            col_index = i
            break
            
    if col_index is not None:
        row[col_index] = value
        logger.info(f"Updated {column_name} with value {value} for collection {row[0]}")
    else:
        logger.error(f"Could not find '{column_name}' column in collection table")


def main(args=None):
 
    logger = create_logger()

    logger.info(f"Started post regression results: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    collection_table = get_regression_sheet_table()

    for row in collection_table:
        print(row)

    header_row = collection_table[0]

    for row in collection_table[1:]:
        short_name, granule_id = row[0], row[1]

        if not granule_id:
            logger.info(f"Skipping collection {short_name} - no granule ID provided")
            continue

        logger.info(f"Processing collection with short_name: {short_name}, granule_id: {granule_id}")

        granule_data = process_granule(short_name, granule_id)
        logger.debug(f"Granule data: {granule_data}")

        insert_value_into_row(row, "Image Count (tig 0.13.0)", header_row, str(granule_data.get('image_counts', {}).get('tig_0.13.0', 'NA')))

        insert_value_into_row(row, "Forge Status", header_row, granule_data['forge_status'])
        insert_value_into_row(row, "TIG Status", header_row, granule_data['tig_status'])
        insert_value_into_row(row, "Forge-py Status", header_row, granule_data['forge_py_status'])

    # Update the entire worksheet with the modified collection table
    worksheet = workbook.worksheet("Regression Tests")
    update_sheet(worksheet, collection_table, 'A1')

    logger.info(f"Finished all collections: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")


if __name__ == "__main__":
    main()
