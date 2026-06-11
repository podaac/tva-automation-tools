import filecmp
import os
import shutil
import cmr
import pytz
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import gspread
import requests
import json
import logging
import sys
from run_step_function import run_step_function
from compare_reference import load_cnm_files, compare

import boto3
from retrying import retry


@dataclass
class DownloadedFile:
    local_path: str
    collection_name: str
    granule_ur: str
    variable: str
    file_type: str
    extension: str

    @property
    def reference_filename(self) -> str:
        return f"{self.granule_ur}_{self.variable}.{self.extension}"

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


def create_logger():
    """Return configured logger from parsed cli args."""

    log_file = "log.txt"
    logging.basicConfig(filename=log_file)
    logger = logging.getLogger("regression_tests")
    logger.setLevel(getattr(logging, "DEBUG"))
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def get_state_machine_arn(aws_profile: str) -> str:
    name = f"podaac-{aws_profile[-3:]}-svc-BrowseImageWorkflow"
    session = boto3.Session(profile_name=aws_profile)
    sfn = session.client('stepfunctions', region_name='us-west-2')

    paginator = sfn.get_paginator('list_state_machines')
    for page in paginator.paginate():
        for sm in page['stateMachines']:
            if sm['name'] == name:
                return sm['stateMachineArn']

    raise ValueError(f"State machine '{name}' not found for profile '{aws_profile}'")


def get_granule(short_name, provider, granule_ur, edl_token, cmr_env):
    mode = cmr.queries.CMR_UAT if cmr_env == 'UAT' else cmr.queries.CMR_OPS
    granule_url = cmr.queries.GranuleQuery(
                    mode=mode).short_name(short_name).provider(provider).granule_ur(granule_ur).format('umm_json')._build_url()

    print(granule_url)
    headers = {"Authorization": f"Bearer {edl_token}"}

    granule = requests.get(granule_url, headers=headers).json()['items']

    if len(granule) == 0:
        raise Exception(f"No granule found with UR {granule_ur} (short_name={short_name}, provider={provider})")
    if len(granule) > 1:
        raise Exception(f"Found {len(granule)} granules with UR {granule_ur} (short_name={short_name}, provider={provider}), expected 1")

    return granule[0]


def generate_cnm(granule, cmr_environment="UAT", client_id="POCLOUD", stack="podaac-ops-cumulus"):
    """
    Generate a CNM (Cloud Notification Message) object from a CMR granule.
    
    Args:
        granule (dict): The granule metadata from CMR in UMM-JSON format
        cmr_environment (str): The CMR environment (e.g., "UAT", "OPS")
        client_id (str): The client ID for CMR
        stack (str): The Cumulus stack name
        
    Returns:
        dict: A CNM object with the structure matching input3.json
    """
    # Extract metadata from granule
    meta = granule.get('meta', {})
    umm = granule.get('umm', {})
    
    concept_id = meta.get('concept-id', '')
    provider_id = meta.get('provider-id', '')
    
    # Get granule ID from GranuleUR in umm
    granule_id = umm.get('GranuleUR', '')
    
    # Get collection name from CollectionReference
    collection_ref = umm.get('CollectionReference', {})
    collection_name = collection_ref.get('ShortName', '')
    
    # Build the CMR link based on environment
    cmr_base = "cmr.uat.earthdata.nasa.gov" if cmr_environment == "UAT" else "cmr.earthdata.nasa.gov"
    cmr_link = f"https://{cmr_base}/search/concepts/{concept_id}.umm_json"
    
    cnm = {
        "cumulus_meta": {},
        "meta": {
            "buckets": {},
            "cmr": {
                "clientId": client_id,
                "cmrEnvironment": cmr_environment,
                "provider": provider_id
            },
            "collection": {
                "name": f"{collection_name}"
            },
            "stack": stack,
            "provider": {}
        },
        "payload": {
            "granules": [
                {
                    "granuleId": granule_id,
                    "provider": provider_id,
                    "cmrLink": cmr_link,
                    "cmrConceptId": concept_id
                }
            ]
        }
    }
    
    return cnm


def get_regression_sheet_table(env: str):

    collections_ws = workbook.worksheet(env)
    collection_table = collections_ws.get_all_values()

    return collection_table


def download_result_cnm_files(workdir: str, output_data: dict, aws_profile: str, logger) -> list[str]:
    session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
    s3 = session.client('s3')

    pobit = output_data.get('payload', {}).get('pobit', [])

    cnm_dir = os.path.join(workdir, 'cnm')
    os.makedirs(cnm_dir, exist_ok=True)

    downloaded_files = []

    for item in pobit:
        cnm_bucket = item.get('cnm_bucket', '')
        cnm_key = item.get('cnm_key', '')
        if not cnm_bucket or not cnm_key:
            continue

        cnm_filename = os.path.basename(cnm_key)
        cnm_local_path = os.path.join(cnm_dir, cnm_filename)

        try:
            logger.info(f"Downloading CNM: s3://{cnm_bucket}/{cnm_key}")
            s3.download_file(cnm_bucket, cnm_key, cnm_local_path)

            cnm_data = json.loads(Path(cnm_local_path).read_text())
            Path(cnm_local_path).write_text(json.dumps(cnm_data, indent=4))

            downloaded_files.append(cnm_local_path)
        except Exception as e:
            logger.error(f"Failed to download CNM s3://{cnm_bucket}/{cnm_key}: {e}")

    logger.info(f"Downloaded {len(downloaded_files)} CNM files to: {cnm_dir}")

    return downloaded_files


def download_result_files(workdir: str, output_data: dict, collection_name: str, granule_ur: str, aws_profile: str) -> list[DownloadedFile]:
    session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
    s3 = session.client('s3')

    pobit = output_data.get('payload', {}).get('pobit', [])

    cnm_dir = os.path.join(workdir, 'cnm')
    files_dir = os.path.join(workdir, 'files')
    os.makedirs(cnm_dir, exist_ok=True)
    os.makedirs(files_dir, exist_ok=True)

    downloaded_files = []

    for item in pobit:
        cnm_bucket = item.get('cnm_bucket', '')
        cnm_key = item.get('cnm_key', '')
        if not cnm_bucket or not cnm_key:
            continue

        cnm_filename = os.path.basename(cnm_key)
        cnm_local_path = os.path.join(cnm_dir, cnm_filename)

        print(f"Downloading CNM: s3://{cnm_bucket}/{cnm_key}")
        s3.download_file(cnm_bucket, cnm_key, cnm_local_path)

        with open(cnm_local_path, 'r') as f:
            cnm_data = json.load(f)

        with open(cnm_local_path, 'w') as f:
            json.dump(cnm_data, f, indent=4)

        for pf in cnm_data.get('product', {}).get('files', []):
            bucket = pf.get('bucket', '')
            key = pf.get('key', '')
            if not bucket or not key:
                continue

            filename = pf.get('fileName', os.path.basename(key))
            local_path = os.path.join(files_dir, filename)

            if not os.path.exists(local_path):
                print(f"  Downloading file: s3://{bucket}/{key}")
                s3.download_file(bucket, key, local_path)

            extension = filename.rsplit('.', 1)[-1] if '.' in filename else ''
            downloaded_files.append(DownloadedFile(
                local_path=local_path,
                collection_name=collection_name,
                granule_ur=granule_ur,
                variable=pf.get('variable', ''),
                file_type=pf.get('type', ''),
                extension=extension,
            ))

    print(f"Downloaded CNM files to: {cnm_dir}")
    print(f"Downloaded {len(downloaded_files)} product files to: {files_dir}")
    return downloaded_files


def compare_with_reference(dl_file, reference_dir: str = 'reference_data') -> bool:
    """Compare downloaded file with reference file.

    Args:
        dl_file: DownloadedFile dataclass instance
        reference_dir: Directory containing reference images (default: reference_data)

    Returns:
        True if files match, False otherwise
    """
    downloaded = Path(dl_file.local_path)

    script_dir = Path(__file__).parent
    reference_path = script_dir / reference_dir / dl_file.collection_name / dl_file.reference_filename

    if not reference_path.exists():
        print(f"Reference image not found: {reference_path}", file=sys.stderr)
        return False

    print("Comparing with Reference:")
    print("-" * 40)
    print(f"Downloaded:  {downloaded}")
    print(f"Reference:   {reference_path}")

    # Compare files byte-by-byte
    match = filecmp.cmp(str(downloaded), str(reference_path), shallow=False)

    if match:
        print("Result:      MATCH - Images are identical")
    else:
        # Get file sizes for additional info
        downloaded_size = downloaded.stat().st_size
        reference_size = reference_path.stat().st_size
        print(f"Result:      MISMATCH - Images differ")
        print(f"  Downloaded size: {downloaded_size} bytes")
        print(f"  Reference size:  {reference_size} bytes")

    return match


def run_one_regression(workdir_root: str, short_name: str, provider: str, granule_ur: str, edl_token: str, cmr_env: str, aws_profile: str, logger) -> dict:

    logger.info(f"Running regression for {short_name} with granule UR: {granule_ur}")

    result = {'stepfunction_status': None, 'compare': ''}

    try:
        granule = get_granule(short_name, provider, granule_ur, edl_token, cmr_env)

        # Clear and recreate the working dir
        workdir = f'{workdir_root}/{short_name}/{granule_ur}/{cmr_env}'
        if os.path.exists(workdir):
            shutil.rmtree(workdir)
        os.makedirs(workdir)

        if 'sit' in aws_profile:
            stack = "podaac-sit-svc"

        cnm = generate_cnm(granule, cmr_environment=cmr_env, stack=stack)
    #    logger.debug(json.dumps(cnm, indent=4))

        Path(f'{workdir}/input.json').write_text(json.dumps(cnm, indent=4))

        state_machine_arn = get_state_machine_arn(aws_profile)

        response = run_step_function(state_machine_arn=state_machine_arn,
                        input_file=f'{workdir}/input.json',
                        region="us-west-2",
                        poll_interval=10,
                        no_wait=False,
                        aws_profile=aws_profile)

        status = response['status']
        result['stepfunction_status'] = 'PASS' if status == 'SUCCEEDED' else 'FAIL'

        if status != 'SUCCEEDED':
            error_info = {
                'status': status,
                'error': response.get('error'),
                'cause': response.get('cause'),
            }
            Path(f'{workdir}/error.json').write_text(json.dumps(error_info, indent=4))

            cause = response.get('cause', '')
            try:
                error_msg = json.loads(cause).get('errorMessage', cause)
            except (json.JSONDecodeError, AttributeError):
                error_msg = cause
            result['compare'] = f"ERROR: {error_msg}"

            logger.warning(f"Step function did not succeed (status={status}); skipping download and comparison.")
            return result

        output = response.get('output')

        # Save the output to a file
        output_data = json.loads(output) if isinstance(output, str) else output
        Path(f'{workdir}/output.json').write_text(json.dumps(output_data, indent=4))

        # Download CNM files from S3
        download_result_cnm_files(workdir=workdir, output_data=output_data, aws_profile=aws_profile, logger=logger)

        # Load current and reference CNM data and compare
        current_cnm_dir = os.path.join(workdir, 'cnm')
        reference_cnm_dir = os.path.join('reference_data', short_name, granule_ur, cmr_env, 'cnm')

        current = load_cnm_files(short_name, granule_ur, cmr_env, current_cnm_dir)
        reference = load_cnm_files(short_name, granule_ur, cmr_env, reference_cnm_dir)
        result['compare'] = compare(reference, current)
        logger.info(result['compare'])

        return result

    except Exception as e:
        logger.error(f"Error running regression for {short_name} ({granule_ur}): {e}")
        result['stepfunction_status'] = 'FAIL'
        error_info = {
            'status': 'ERROR',
            'error': type(e).__name__,
            'cause': str(e),
        }
        try:
            Path(f'{workdir}/error.json').write_text(json.dumps(error_info, indent=4))
        except Exception:
            pass
        return result


def run_regressions(cmr_env: str, logger, aws_profile: str):

    logger.info(f"Started regression tests ({aws_profile}) ({cmr_env}): "                         # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    edl_token = bearer_token(cmr_env.lower(), logger)

    # Create workdir subdirectory if it doesn't exist
    workdir_root = f"workdir"
    if not os.path.exists(workdir_root):
        os.makedirs(workdir_root)

    worksheet = workbook.worksheet(f"CMR {cmr_env}")
    collection_table = worksheet.get_all_values()

    for row_idx, row in enumerate(collection_table[1:], start=2):
        skip = row[1]

        if skip != 'X':
            short_name = row[0]
            provider = row[2]
            granule_ur = row[3]

            result = run_one_regression(workdir_root, short_name, provider, granule_ur, edl_token, cmr_env, aws_profile, logger)

            logger.info(f"Regression for {short_name} completed with status: {result['stepfunction_status']}")

            row_data = [result['stepfunction_status'], result['compare']]
            update_sheet(worksheet, [row_data], f'E{row_idx}')

            if result['stepfunction_status'] != 'PASS':
                logger.warning(f"Regression for {short_name} failed")

            print()


def main(args=None):

    logger = create_logger()

    run_regressions("UAT", logger, 'podaac-services-sit')
#    run_regressions("OPS", logger, 'podaac-services-sit')


if __name__ == "__main__":
    main()
