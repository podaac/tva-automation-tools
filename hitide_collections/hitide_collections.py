import argparse
import csv
import json
import os
import requests
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import boto3
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

def read_csv_file(filename):
    data = []
    with open(filename, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            data.extend([row])
    return data

class HitideCollections:

    def __init__(self, logger, env, data_path):

        self.logger = logger

        self.env = env
        self.data_path = data_path

        self.collections = {}

        self.hitide_associations_text = []

        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session = Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Get bearer tokens
        token = self.bearer_token()

        if not token:
            print("Could not get bearer token")
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

        self.get_association_text_collections()

        try:
            self.get_cumulus_api_workflow_choices()
        except Exception as ex:
            self.logger.error(ex)
            error_list.append([f"NA ({self.env.upper()})", str(ex), ex.__traceback__.tb_lineno])
            self.cumulus_configurations_from_api = {}


    def add_collections(self, umm_name, collections_query):

        collections = [(a.get('id'), a.get('short_name'), a.get("associations").get("variables") if a.get("associations") else None, a.get("watch_status"))
                        for a in collections_query]
        collections = sorted(collections, key=lambda tup: tup[1])

        for collection in collections:
            id = collection[0]
            if id not in self.collections:
                self.collections[id] = {'short_name': collection[1]}

            if "L2SS-py" in umm_name:
                self.collections[id]['l2ss_concise_chain'] = "X"
            elif "Subsetter" in umm_name:
                self.collections[id]['l2ss'] = "X"
            elif "Concise" in umm_name:
                self.collections[id]['concise'] = "X"
            elif "HiTIDE" in umm_name:
                self.collections[id]['hitide'] = "X"

            if collection[2] is not None and len(collection[2]) > 0:
                self.collections[id]['umm_v_count'] = len(collection[2])

            if collection[3] == "Coming Soon":
                self.collections[id]['coming_soon'] = "X"


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
            concept_id = cmr.queries.ServiceQuery(mode=mode).provider(
                'POCLOUD').name(umm_name).get()[0].get('concept_id')
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
        header_row.append('Coming Soon')
        header_row.append('HiTIDE UI')
        header_row.append('HiTIDE TXT')
        header_row.append('L2SS Subsetter')
        header_row.append('L2SS TXT')
        header_row.append('Concise')
        header_row.append('Concise TXT')
        header_row.append('L2SS Concise Chain')
        header_row.append('Forge Tig Config')
        header_row.append('Footprint Config')
        header_row.append('UMM-V')
        header_row.append('UMM-V Lat')
        header_row.append('UMM-V Lon')
        header_row.append('Config Thumbnails')
        header_row.append('Last Granule Thumbnails')
        header_row.append('Granules')
        header_row.append('Last Granule')
        header_row.append('Footprint GPolygons')
        header_row.append('Footprint BBox')
        header_row.append('Footprint Lines')
        header_row.append('Cumulus Footprint')
        header_row.append('Cumulus Image')
        header_row.append('Cumulus DMRPP')

        records = [header_row]

        max_length = 0
        for id, collection in sorted(self.collections.items(), key=lambda x: x[1]['short_name']):

            short_name = collection.get('short_name')

            if len(short_name) > max_length:
                max_length = len(short_name)

            row = [short_name]
            row.append(id)
            row.append(collection.get('coming_soon'))
            row.append(collection.get('hitide'))
            row.append(collection.get('hitide_txt'))
            row.append(collection.get('l2ss'))
            row.append(collection.get('l2ss_txt'))
            row.append(collection.get('concise'))
            row.append(collection.get('concise_txt'))
            row.append(collection.get('l2ss_concise_chain'))
            row.append(collection.get('forge_tig_config'))
            row.append(collection.get('footprint_config'))
            row.append(collection.get('umm_v_count'))
            row.append(collection.get('umm_v_lat'))
            row.append(collection.get('umm_v_lon'))
            row.append(collection.get('thumbnail_count'))
            row.append(collection.get('last_granule_thumbnail_count'))
            row.append(collection.get('granule_count'))
            row.append(collection.get('last_granule_date'))
            row.append(collection.get('last_granule_gpolygon'))
            row.append(collection.get('last_granule_bbox'))
            row.append(collection.get('last_granule_lines'))
            row.append(collection.get('cumulus_footprint'))
            row.append(collection.get('cumulus_image'))
            row.append(collection.get('cumulus_dmrpp'))

            records.append(row)

        if self.env == 'ops':
            worksheet = workbook.worksheet("OPS")
        else:
            worksheet = workbook.worksheet("UAT")

        worksheet.clear()
        worksheet.update(records, "A1")

        set_column_width(worksheet, 'A', 7*max_length)
        set_column_width(worksheet, 'B', 8*len(records[0][1]))
        set_column_width(worksheet, 'C', 8*len(records[0][2]) + 6)
        set_column_width(worksheet, 'D', 8*len(records[0][3]))
        set_column_width(worksheet, 'E', 8*len(records[0][4]))
        set_column_width(worksheet, 'F', 8*len(records[0][5]))
        set_column_width(worksheet, 'G', 9*len(records[0][6]))
        set_column_width(worksheet, 'H', 9*len(records[0][7]))
        set_column_width(worksheet, 'I', 8*len(records[0][8]))
        set_column_width(worksheet, 'J', 8*len(records[0][9]))
        set_column_width(worksheet, 'K', 7*len(records[0][10]))
        set_column_width(worksheet, 'L', 7*len(records[0][11]))
        set_column_width(worksheet, 'M', 10*len(records[0][12]) + 6)
        set_column_width(worksheet, 'N', 9*len(records[0][13]))
        set_column_width(worksheet, 'O', 9*len(records[0][14]))
        set_column_width(worksheet, 'P', 7*len(records[0][15]) + 7)
        set_column_width(worksheet, 'Q', 7*len(records[0][16]) + 6)
        set_column_width(worksheet, 'R', 8*len(records[0][17]))
        set_column_width(worksheet, 'S', 7*len(records[0][18]) + 6)
        set_column_width(worksheet, 'T', 7*len(records[0][19]) + 6)
        set_column_width(worksheet, 'U', 7*len(records[0][20]) + 6)
        set_column_width(worksheet, 'V', 7*len(records[0][21]) + 4)
        set_column_width(worksheet, 'W', 8*len(records[0][22]))
        set_column_width(worksheet, 'X', 9*len(records[0][23]))
        set_column_width(worksheet, 'Y', 9*len(records[0][24]))


    def get_association_text_collections(self):

        hitide_url = f"https://raw.githubusercontent.com/podaac/hitide-ui/develop/cmr/{self.env}_associations.txt"

        self.hitide_associations_text = self.session.get(hitide_url).text.split('\n')


    def has_l2ss_association(self, concept_id):

        url = f"https://raw.githubusercontent.com/podaac/l2ss-py-autotest/main/tests/cmr/l2ss-py/{self.env}/{concept_id}"

        response = self.session.get(url)

        if response.status_code == 200:
            return True
        
        return False


    def has_concise_association(self, concept_id):

        url = f"https://raw.githubusercontent.com/podaac/concise-autotest/main/tests/cmr/concise/{self.env}/{concept_id}"

        response = self.session.get(url)

        if response.status_code == 200:
            return True
        
        return False


    def add_cumulus_footprint_image(self):

        cumulus_collections = [
            name for name, workflow in self.cumulus_configurations_from_api.items()
            if workflow.get('image') or workflow.get('footprint')
        ]

        print(cumulus_collections)
        print("Cumulus Configs Collection Count = " + str(len(cumulus_collections)))

        if self.env == "ops":
            mode = cmr.queries.CMR_OPS
        else:
            mode = cmr.queries.CMR_UAT

        for short_name in cumulus_collections:
            if not any(attributes.get("short_name") == short_name for attributes in self.collections.values()):
                print(f"Adding {short_name} via Cumulus Config...")
                url = cmr.queries.CollectionQuery(
                    mode=mode).provider('POCLOUD').short_name(short_name)._build_url()

                collections_query = self.session.get(url, headers=self.headers, params={
                                                'page_size': 1}).json()['feed']['entry']

                self.add_collections("", collections_query)


    def list_github_files(self, repo: str, path: str, branch: str = "main"):
        """List all files in a GitHub repository directory.

        Args:
            repo (str): Repository name.
            path (str): Path to the directory in the repo.
            branch (str, optional): Branch name. Defaults to 'main'.

        Returns:
            list: A list of file URLs.
        """
        url = f"https://api.github.com/repos/podaac/{repo}/contents/{path}?ref={branch}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            files = response.json()
            return [file["download_url"] for file in files if file["type"] == "file"]
        else:
            raise Exception(f"Failed to fetch files: {response.status_code}, {response.text}")


    def add_concept_ids(self, concept_ids):

        if self.env == "ops":
            mode = cmr.queries.CMR_OPS
        else:
            mode = cmr.queries.CMR_UAT

        for concept_id in concept_ids:
            try:
                url = cmr.queries.CollectionQuery(
                        mode=mode).provider('POCLOUD').concept_id(concept_id)._build_url()

                collections_query = self.session.get(url, headers=self.headers, params={
                                                'page_size': 1}).json()['feed']['entry']

                self.add_collections("", collections_query)
            except Exception as ex:
                print(ex)
                print(concept_id)
                pass
    

    def add_configs(self):

        # Add collections from forge tig config files
        s3_url = f"s3://podaac-services-{self.env}-hitide/dataset-configs"
    
        forge_tig_config_files = self.s3.list_s3_keys(s3_url)
        short_names = [path.split("/")[1].rsplit(".", 1)[0] for path in forge_tig_config_files]

        if self.env == "ops":
            mode = cmr.queries.CMR_OPS
        else:
            mode = cmr.queries.CMR_UAT

        for short_name in short_names:
            try:
                url = cmr.queries.CollectionQuery(
                    mode=mode).provider('POCLOUD').short_name(short_name)._build_url()

                collections_query = self.session.get(url, headers=self.headers, params={
                                                'page_size': 1}).json()['feed']['entry']

                self.add_collections("", collections_query)
            except Exception as ex:
                print(ex)
                print(short_name)
                pass

        # Add collections from hitide-ui txt associations file
        self.add_concept_ids(self.hitide_associations_text)

        # Add collections from l2ss-py-autotest txt associations files
        l2ss_autotest_id_files = self.list_github_files("l2ss-py-autotest", f"tests/cmr/l2ss-py/{self.env}")
        l2ss_concept_ids = [path.split("/")[-1] for path in l2ss_autotest_id_files]
        self.add_concept_ids(l2ss_concept_ids)

        # Add collections from concise-autotest txt associations files
        concise_autotest_id_files = self.list_github_files("concise-autotest", f"tests/cmr/concise/{self.env}")
        concise_concept_ids = [path.split("/")[-1] for path in concise_autotest_id_files]
        self.add_concept_ids(concise_concept_ids)


    def add_watches(self):

        watch_collections = read_csv_file(f"{self.data_path}/watch.csv")

        if self.env == "ops":
            mode = cmr.queries.CMR_OPS
        else:
            mode = cmr.queries.CMR_UAT

        for row in watch_collections:
            short_name = row[0]

            url = cmr.queries.CollectionQuery(
                mode=mode).provider('POCLOUD').short_name(short_name)._build_url()

            try:
                collections_query = self.session.get(url, headers=self.headers, params={
                                                'page_size': 1}).json()['feed']['entry']

                if len(row) > 1:
                    collections_query[0]['watch_status'] = row[1]

                self.add_collections("", collections_query)
            except Exception as ex:
                print(ex)
                print(short_name)
                pass

    def get_cumulus_api_workflow_choices(self):
        """Function to invoke cumulus api via aws lambda"""

        prefix = f"podaac-{self.env}-cumulus"
        profile = f"ngap-cumulus-{self.env}"
        session = boto3.Session(profile_name=profile)
        client = session.client('lambda')

        all_results = []
        page = 1  # Start with page 1 or 100 as per your requirement
        limit = 50  # Number of results per page

        while True:
            payload = {
                'httpMethod': 'GET',
                'resource': '/{proxy+}',
                'path': '/collections',
                'queryStringParameters': {
                    'limit': str(limit),
                    'page': str(page),
                    'fields': 'name,meta.workflowChoice.dmrpp,meta.workflowChoice.footprint,meta.workflowChoice.image'
                }
            }

            response = client.invoke(
                FunctionName='{}-PrivateApiLambda'.format(prefix),
                Payload=json.dumps(payload),
            )

            json_response_payload = response.get('Payload').read().decode('utf-8')
            response_data = json.loads(json_response_payload)
            
            # Extract the body and data from the response
            data = json.loads(response_data.get('body'))

            # Append the results from this page to the all_results list
            all_results.extend(data.get('results', []))

            # Check if there are more results to fetch
            if len(data.get('results', [])) < limit:
                # If fewer results than the limit, we assume it's the last page
                break

            # Move to the next page
            page += 1

        formatted_data = {
            item['name']: item.get('meta', {}).get('workflowChoice', {}) for item in all_results
        }

        self.cumulus_configurations_from_api = formatted_data

    def umm_update_one_collection(self, item):
        
        try:
            concept_id = item[0]
            collection = item[1]

            short_name = collection.get('short_name')

            print(f"Updating {self.env} collection...{concept_id} ({short_name})")

            try:
                collection_config = f"s3://podaac-services-{self.env}-hitide/dataset-configs/{short_name}.cfg"

                config = self.s3.read_file_from_s3(collection_config)
                forge_tig_config = json.loads(config)

                collection['forge_tig_config'] = "X"

                if forge_tig_config.get('footprint'):
                    collection['footprint_config'] = "X"

                if forge_tig_config.get('imgVariables'):
                    collection['thumbnail_count'] = len(forge_tig_config.get('imgVariables'))
                else:
                    collection['thumbnail_count'] = 0
            except Exception as ex:
                self.logger.error(ex)
                pass

            cumulus_config = self.cumulus_configurations_from_api.get(short_name)

            if cumulus_config is not None and cumulus_config.get('footprint'):
                collection['cumulus_footprint'] = "X"

            if cumulus_config is not None and cumulus_config.get('image'):
                collection['cumulus_image'] = "X"

            if cumulus_config is not None and cumulus_config.get('dmrpp'):
                collection['cumulus_dmrpp'] = "X"

            collection['hitide_txt'] = "X" if concept_id in self.hitide_associations_text else ""
            collection['l2ss_txt'] = "X" if self.has_l2ss_association(concept_id) else ""
            collection['concise_txt'] = "X" if self.has_concise_association(concept_id) else ""

            graphql_query = execute_graphql_query(concept_id, self.env, self.headers)

            granules = graphql_query.get('collections').get('items')[0].get('granules')

            collection['granule_count'] = granules.get("count")

            variables = graphql_query.get('collections').get('items')[0].get('variables').get('items')

            if len(granules.get("items")) > 0:
                last_granule = granules.get("items")[0]

                geometry = last_granule.get('spatialExtent').get('horizontalSpatialDomain').get('geometry')

                if geometry:
                    if any(key.lower() == 'gpolygons' for key in geometry):
                        collection['last_granule_gpolygon'] = "X"

                    if 'boundingRectangles' in geometry:
                        collection['last_granule_bbox'] = "X"

                    if 'lines' in geometry:
                        collection['last_granule_lines'] = "X"
                else:
                    #TODO: Add column for FP Orbit?
                    orbit = last_granule.get('spatialExtent').get('horizontalSpatialDomain').get('orbit')
                    if orbit:
                        print(f"Found orbit for {short_name}")

                collection['last_granule_date'] = last_granule.get('temporalExtent').get('rangeDateTime').get('endingDateTime')[:10]

                var_names = [var['name'] for var in variables] if variables is not None else []

                if 'thumbnail_count' in collection:
                    collection['last_granule_thumbnail_count'] = sum(   any(name.replace('/', '.') in url.get('url') for name in var_names) and
                                                                        url.get('mimeType') == "image/png" and
                                                                        url.get('type') == "GET RELATED VISUALIZATION" and
                                                                        url.get('subtype') == "DIRECT DOWNLOAD"
                                                                        for url in last_granule.get('relatedUrls'))

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
            print("Error: " + str(e))

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
            print(ex)
            print(f"Error getting the {self.env} token - check user name and password")

        # No tokens exist, try to create one
        if not tokens:
            try:
                resp = self.session.post(url + "/token", headers=headers,
                                            auth=requests.auth.HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
                response_content: dict = json.loads(resp.content)
                tokens.append(response_content['access_token'])
            except Exception as ex:  # noqa E722
                print(ex)
                print(f"Error getting the {self.env} token - check user name and password")

        # If still no token, then we can't do anything
        if not tokens:
            return None

        return next(iter(tokens))


    def run(self):

        self.add_watches()
        self.update_associations("PODAAC L2 Cloud Subsetter", "service")
        self.update_associations("PODAAC Concise", "service")
        self.update_associations("PODAAC L2SS-py Concise Chain", "service")
        self.update_associations("HiTIDE", "tool")
        self.add_cumulus_footprint_image()
        self.add_configs()
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

    parser.add_argument('-d', '--data',
                        help='path to data folder',
                        required=True,
                        metavar='')

    args = parser.parse_args()
    return args


if __name__ == '__main__':

    _args = parse_args()

    logger = logger_from_args(_args)

    hitide_collections_ops = HitideCollections(logger, "ops", _args.data)
    hitide_collections_ops.run()

    hitide_collections_uat = HitideCollections(logger, "uat", _args.data)
    hitide_collections_uat.run()

    status_ws = workbook.worksheet("Status")
    status_ws.clear()

    status = [[]]
    status.append(["Last Updated"])
    status.append([])
    status.append(["Errors", "Collection", "Message", "Line Number"])

    status_ws.update("A1", status)

    now = datetime.now(pytz.timezone('US/Pacific'))
    dt_string = now.strftime("%m/%d/%Y %I:%M:%S %p")

    status_ws.update("B2", [[dt_string]], value_input_option='USER_ENTERED')

    if len(error_list) > 0:
        status_ws.update("B5", error_list)
    else:
        status_ws.update("B5", [["None"]])
