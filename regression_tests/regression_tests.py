import os
import cmr
import pytz
from datetime import datetime
import gspread
import subprocess
import requests
import json
import logging
import sys

from retrying import retry


gc = gspread.service_account()

spreadsheet_id = os.environ['SPREADSHEET_ID']
DATASET_CONFIG_URL = "https://hitide.podaac.earthdatacloud.nasa.gov/dataset-configs/"

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


def get_collection_config(short_name):

    collection_config = DATASET_CONFIG_URL + short_name + '.cfg'
    forge_tig_config_resp = requests.get(collection_config)

    if forge_tig_config_resp.status_code == 200:
        forge_tig_config = forge_tig_config_resp.json()

        return forge_tig_config


def save_config(dir):
    # Get short_name from the base directory name
    short_name = os.path.basename(dir)

    config = get_collection_config(short_name)

    with open(os.path.join(dir, short_name + '.cfg'), 'w') as f:
        json.dump(config, f, indent=4)


def get_granule(granule_id, edl_token):
    """
    Get a specific granule from CMR by granule ID.
    
    Args:
        granule_id (str): The ID of the granule to retrieve
        edl_token (str): EDL bearer token for authentication
        
    Returns:
        dict: The granule metadata from CMR
        
    Raises:
        Exception: If no granule is found with the given ID
    """
    mode = cmr.queries.CMR_OPS
    granule_url = cmr.queries.GranuleQuery(
                    mode=mode).provider('POCLOUD').concept_id(granule_id).format('umm_json')._build_url()

    print(granule_url)
    headers = {"Authorization": f"Bearer {edl_token}"}

    granule = requests.get(granule_url, headers=headers).json()['items']

    if len(granule) != 1:
        print(f"No granule found with ID {granule_id}")
        raise Exception(f"No granule found with ID {granule_id}")
    
    return granule[0]


def get_last_granule(short_name, edl_token):

    mode = cmr.queries.CMR_OPS
    granule_url = cmr.queries.GranuleQuery(
                    mode=mode).provider('POCLOUD').short_name(short_name).format('umm_json')._build_url()
    
    print(granule_url)
    headers = {"Authorization": f"Bearer {edl_token}"}

 #   first_granule = requests.get(granule_url, headers=headers, params={
 #                               'page_size': 1, 'sort_key': 'start_date'}).json()['items']
    last_granule = requests.get(granule_url, headers=headers, params={
                                'page_size': 1, 'sort_key': '-start_date'}).json()['items']

 #  granule_count = requests.get(granule_url, headers=headers, params={
  #                              'page_size': 0}).headers["CMR-Hits"]

 #   print('granule counts = ' + granule_count)
 #   print(last_granule)

    if len(last_granule) != 1:
        print("No granules found for " + short_name)
        raise Exception("No granules found for " + short_name)
    
    
    return last_granule[0]


def bearer_token(env: str, logger) -> str:
    url = f"https://{'uat.' if env == 'uat' else ''}urs.earthdata.nasa.gov/api/users/find_or_create_token"

    try:
        # Make the request with the Base64-encoded Authorization header
        resp = requests.post(
            url,
            auth=requests.auth.HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS'])
        )

        # Check for successful response
        if resp.status_code == 200:
            response_content = resp.json()
            return response_content.get('access_token')

    except Exception as e:
        logger.error(f"Error getting the token (status code {resp.status_code}): {e}", exc_info=True)


def get_info(granule_json):

    related_urls = granule_json.get('umm').get('RelatedUrls')

    granule_url = None
    for x in related_urls:
        if x.get('Type') == "GET DATA" and x.get('Subtype') in [None, 'DIRECT DOWNLOAD'] and '.bin' not in x.get('URL'):
            granule_url = x.get('URL')

    return { 'href': granule_url,
            'id': granule_json.get('meta').get('concept-id')}


def download_file(save_path, source_url, edl_token):
    """
    Download a file from a URL to a specified path, using EDL token authentication.
    
    Args:
        save_path (str): Path where the file should be saved
        source_url (str): URL of the file to download
        edl_token (str): EDL bearer token for authentication
    """
    # Create session and set authorization header with token
    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {edl_token}'})

    try:
        # Stream the download to handle large files efficiently
        response = session.get(source_url, stream=True)
        response.raise_for_status()
        
        # Get the filename from the URL
        filename = os.path.basename(source_url)
        full_path = os.path.join(save_path, filename)
        
        # Write the file in chunks
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Downloaded file to {full_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        raise


def fill_regression(workdir, edl_token):
    collection_table = get_regression_sheet_table()

    print(collection_table)
    print(len(collection_table))

    header = ['Granule ID']
    header.append('Lock Granule')
    header.append('Data URL')
    header.append('Config Image Count')
    rows = [header]

    # Process each row in collection table, skipping header row
    for collection_row in collection_table[1:]:
        row = []

        try:
            short_name = collection_row[0]
            is_lock_granule = collection_row[2]

            if is_lock_granule == 'X':
                granule_id = collection_row[1]
                granule = get_granule(granule_id, edl_token)
            else:
                granule = get_last_granule(short_name, edl_token)

            info = get_info(granule)

            id = info['id']
            
            row.append(id)
            row.append(is_lock_granule)
            row.append(info['href'])

            print("Collection: " + short_name)
            print(row)
            print()

            workdir_collection = f"{workdir}/{short_name}"
            if not os.path.exists(workdir_collection):
                os.makedirs(workdir_collection)

            config_path = os.path.join(workdir_collection, f"{short_name}.cfg")
            if not os.path.exists(config_path):
                save_config(workdir_collection)
            else:
                print(f"Config file {short_name}.cfg already exists, skipping download")

            workdir_granule = f"{workdir_collection}/{id}"
            if not os.path.exists(workdir_granule):
                os.makedirs(workdir_granule)

            filename = os.path.basename(info['href'])
            full_path = os.path.join(workdir_granule, filename)
            if not os.path.exists(full_path):
                download_file(workdir_granule, info['href'], edl_token)
            else:
                print(f"File {filename} already exists, skipping download")

            try:
                with open(config_path) as f:
                    forge_tig_config = json.loads(f.read())

                img_vars = forge_tig_config.get('imgVariables', [])
                thumbnail_count = '-' if not img_vars else len(img_vars)
                row.append(thumbnail_count)
            except Exception as ex:
                pass

        except Exception as e:
            print(f"Warning: {e} Could not add collection {short_name}.  No granules maybe...")

        finally:
            rows.append(row)

    regression_sheet = workbook.worksheet("Regression Tests")

    try:
        update_sheet(regression_sheet, rows,  "B1")
    except RetryError:
        print("Update failed after multiple retries. You may want to handle this error further.")


def create_logger():
    """Return configured logger from parsed cli args."""

    log_file = "log.txt"
    logging.basicConfig(filename=log_file)
    logger = logging.getLogger("regression_tests")
    logger.setLevel(getattr(logging, "DEBUG"))
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def main(args=None):
 
    logger = create_logger()

    logger.info(f"Started regression tests: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    edl_token = bearer_token('ops', logger)

    # Create workdir subdirectory if it doesn't exist
    workdir = "workdir"
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    fill_regression(workdir, edl_token)

    logger.info(f"Finished all collections: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")


if __name__ == "__main__":
    main()
