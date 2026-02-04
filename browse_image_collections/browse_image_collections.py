import argparse
import json
import os
import requests
import traceback
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import cmr
import gspread
import pytz
from gspread_formatting import set_column_width
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from graphql_query import execute_graphql_query

from podaac.hitide_backfill_tool.s3_reader import S3Reader
from podaac.hitide_backfill_tool.cli import logger_from_args

gc = gspread.service_account()

spreadsheet_id = os.environ['SPREADSHEET_ID']

workbook = gc.open_by_key(spreadsheet_id)

error_list = []

class BrowseImageCollections:

    def __init__(self, logger: logging.Logger, env: str):
        """Initialize HitideCollections.
        
        Args:
            logger: Logger instance for logging
            env: Environment ('ops' or 'uat')
        """
        self.logger: logging.Logger = logger
        self.env: str = env

        self.collections = {}

        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session = Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Get bearer tokens
        token = self.bearer_token()

        if not token:
            self.logger.error("Could not get bearer token")
            exit(1)
        
        self.headers = {'Authorization': f"Bearer {token}"}

        # Setup S3 access to read data-config files
        aws_profile = f"podaac-services-{self.env}"

        try:
            self.s3  = S3Reader(self.logger, aws_profile)
        except Exception as ex:
            self.logger.error(ex)
            error_list.append([f"NA ({self.env.upper()})", str(ex), ex.__traceback__.tb_lineno])
            self.s3 = None


    def add_collections(self, umm_name, collections_query):

        collections = [(a.get('id'), a.get('short_name'), a.get('data_center'), a.get("associations").get("variables") if a.get("associations") else None)
                        for a in collections_query]
        collections = sorted(collections, key=lambda tup: tup[1])

        for collection in collections:
            id = collection[0]
            if id not in self.collections:
                self.collections[id] = {'short_name': collection[1]}

            if "IMAGENATOR-L2" in umm_name:
                self.collections[id]['imagenator_l2'] = "X"
            elif "IMAGENATOR-L3" in umm_name:
                self.collections[id]['imagenator_l3'] = "X"
            elif "HyBIG" in umm_name:
                self.collections[id]['hybig'] = "X"

            self.collections[id]['provider'] = collection[2]

            if collection[3] is not None and len(collection[3]) > 0:
                self.collections[id]['umm_v_count'] = len(collection[3])


    def update_associations(self, umm_name, umm_type):

        if self.env == "ops":
            mode = cmr.queries.CMR_OPS
        else:
            mode = cmr.queries.CMR_UAT

        if umm_type == "tool":
            concept_id = cmr.queries.ToolQuery(mode=mode).provider(
                'POCLOUD').name(umm_name).get()[0].get('concept_id')
            url = cmr.queries.CollectionQuery(
                mode=mode).tool_concept_id(concept_id)._build_url()
        else:
            if umm_name == "HyBIG" and self.env == "uat":
                # This service is named differently in UAT
                umm_name = "Harmony Browse Image Generator (HyBIG)"

            concept_id = cmr.queries.ServiceQuery(mode=mode).name(umm_name).get()[0].get('concept_id')
            url = cmr.queries.CollectionQuery(
                mode=mode).service_concept_id(concept_id)._build_url()

        collections_query = self.session.get(url, headers=self.headers, params={
                                        'page_size': 2000}).json()['feed']['entry']

        self.add_collections(umm_name, collections_query)


    def update_collections(self):

        with ThreadPoolExecutor() as executor:
            executor.map(self.umm_update_one_collection, self.collections.items())


    def write_worksheet_collection(self):

        header_row = ['Collection Name']
        header_row.append('Collection Concept ID')
        header_row.append('Worldview')
        header_row.append('Imagenator L2')
        header_row.append('Imagenator L3')
        header_row.append('HyBIG')
        header_row.append('Bignbit Config')
        header_row.append('UMM-V')
        header_row.append('UMM-V Lat')
        header_row.append('UMM-V Lon')
        header_row.append('Granules')

        records = [header_row]

        max_length = 0
        for id, collection in sorted(self.collections.items(), key=lambda x: x[1]['short_name']):

            short_name = collection.get('short_name')

            if len(short_name) > max_length:
                max_length = len(short_name)

            row = [short_name]
            row.append(id)
            row.append(collection.get('worldview'))
            row.append(collection.get('imagenator_l2'))
            row.append(collection.get('imagenator_l3'))
            row.append(collection.get('hybig'))
            row.append(collection.get('bignbit_config'))
            row.append(collection.get('umm_v_count'))
            row.append(collection.get('umm_v_lat'))
            row.append(collection.get('umm_v_lon'))
            row.append(collection.get('granule_count'))

            print(collection)
            records.append(row)

        if self.env == 'ops':
            worksheet = workbook.worksheet("OPS")
        else:
            worksheet = workbook.worksheet("UAT")

        worksheet.clear()
        worksheet.update(records, "A1")

        set_column_width(worksheet, 'A', 9*max_length)
        set_column_width(worksheet, 'B', 9*len(records[0][1]))
        set_column_width(worksheet, 'C', 8*len(records[0][2]) + 6)
        set_column_width(worksheet, 'D', 8*len(records[0][3]))
        set_column_width(worksheet, 'E', 8*len(records[0][4]))
        set_column_width(worksheet, 'F', 11*len(records[0][5]))
        set_column_width(worksheet, 'G', 8*len(records[0][6]))
        set_column_width(worksheet, 'H', 11*len(records[0][7]))
        set_column_width(worksheet, 'I', 9*len(records[0][8]))
        set_column_width(worksheet, 'J', 9*len(records[0][9]))
        set_column_width(worksheet, 'K', 9*len(records[0][10]))


    def umm_update_one_collection(self, item):
        
        try:
            concept_id = item[0]
            collection = item[1]

            short_name = collection.get('short_name')

            self.logger.info(f"Updating {self.env} collection...{concept_id} ({short_name})")

            try:
                collection_config = f"s3://podaac-{self.env}-{'svc' if self.env == 'uat' else 'cumulus'}-internal/big-config/{short_name}.cfg"

                config = self.s3.read_file_from_s3(collection_config)

                bignbit_config = json.loads(config)
                print(bignbit_config)
                print(f"Found bignbit config for {short_name}")
                collection['bignbit_config'] = "X"
            except Exception as ex:
                pass

            graphql_query = execute_graphql_query(concept_id, self.env, self.headers)

            granules = graphql_query.get('collections').get('items')[0].get('granules')

            collection['granule_count'] = granules.get("count")

            variables = graphql_query.get('collections').get('items')[0].get('variables').get('items')

            if variables:
                if any(var['name'] == 'lat' or var['name'] == 'latitude' for var in variables):
                    collection['umm_v_lat'] = "X"
                elif any(var['variableType'] == 'COORDINATE' and var['variableSubType'] == 'LATITUDE' for var in variables):
                    collection['umm_v_lat'] = "X"

                if any(var['name'] == 'lon' or var['name'] == 'longitude' for var in variables):
                    collection['umm_v_lon'] = "X"
                elif any(var['variableType'] == 'COORDINATE' and var['variableSubType'] == 'LONGITUDE' for var in variables):
                    collection['umm_v_lon'] = "X"

        except Exception as e:
            self.logger.error("Error: " + str(e))

            # Print the full traceback
            traceback.print_exc()

            error_list.append([f"{short_name} ({self.env.upper()})", str(e), e.__traceback__.tb_lineno])


    def bearer_token(self):
        tokens = []
        headers: dict = {'Accept': 'application/json'}
        url: str = f"https://{'uat.' if self.env == 'uat' else ''}urs.earthdata.nasa.gov/api/users"

        # First just try to get a token that already exists
        try:
            resp = self.session.get(url + "/tokens", headers=headers,
                                    auth=requests.auth.HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
            response_content = json.loads(resp.content)

            for x in response_content:
                tokens.append(x['access_token'])

        except Exception as ex:  # noqa E722
            self.logger.error(ex)
            self.logger.error(f"Error getting the {self.env} token - check user name and password")

        # No tokens exist, try to create one
        if not tokens:
            try:
                resp = self.session.post(url + "/token", headers=headers,
                                            auth=requests.auth.HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
                response_content: dict = json.loads(resp.content)
                tokens.append(response_content['access_token'])
            except Exception as ex:  # noqa E722
                self.logger.error(ex)
                self.logger.error(f"Error getting the {self.env} token - check user name and password")

        # If still no token, then we can't do anything
        if not tokens:
            return None

        return next(iter(tokens))


    def run(self):

        self.update_associations("IMAGENATOR-L2", "service")
        self.update_associations("IMAGENATOR-L3", "service")
        self.update_associations("HyBIG", "service")
        self.update_collections()
        self.write_worksheet_collection()


def parse_args():
    """
    Parses the program arguments
    Returns
    -------
    args
    """

    parser = argparse.ArgumentParser(
        description='Update CMR with latest profile',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--log-file',
                        default='log.txt')
    
    parser.add_argument("--log-level",
                        default="DEBUG")

    args = parser.parse_args()
    return args


if __name__ == '__main__':

    _args = parse_args()

    logger = logger_from_args(_args)

    browse_image_collections_ops = BrowseImageCollections(logger, "ops")
    browse_image_collections_ops.run()

    browse_image_collections_uat = BrowseImageCollections(logger, "uat")
    browse_image_collections_uat.run()

    status_ws = workbook.worksheet("Status")
    status_ws.clear()

    status = [[]]
    status.append(["Last Updated"])
    status.append([])
    status.append(["Errors", "Collection", "Message", "Line Number"])

    status_ws.update(status, "A1")

    now = datetime.now(pytz.timezone('US/Pacific'))
    dt_string = now.strftime("%m/%d/%Y %I:%M:%S %p")

    status_ws.update([[dt_string]], "B2", value_input_option='USER_ENTERED')

    if len(error_list) > 0:
        status_ws.update(error_list, "B5")
    else:
        status_ws.update([["None"]], "B5")
