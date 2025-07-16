from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Lock
import os
import cmr
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
import random
import gspread

from shapely.geometry import box
from pyproj import Geod

import uuid
from retrying import retry

from podaac.hitide_backfill_tool.args import parse_args
from podaac.hitide_backfill_tool.s3_reader import S3Reader
from podaac.hitide_backfill_tool.cli import *


# Define the WGS84 ellipsoid
geod = Geod(ellps="WGS84")
EARTH_AREA_KM2 = 510_065_622  # WGS84 ellipsoid surface area

gc = gspread.service_account()

lock = Lock()

spreadsheet_id = os.environ['SPREADSHEET_ID']
DATASET_CONFIG_URL = "https://hitide.podaac.earthdatacloud.nasa.gov/dataset-configs/"

workbook = gc.open_by_key(spreadsheet_id)

now = datetime.now(pytz.timezone('US/Pacific'))
current_month = now.strftime("%Y-%m")

# Now, create or open a worksheet in the spreadsheet
worksheet_title = "Monthly Counts " + current_month
new_monthly_count_sheet = False
try:
    monthly_counts_sheet = workbook.worksheet(worksheet_title)
except gspread.WorksheetNotFound:
    monthly_counts_sheet = None
    new_monthly_count_sheet = True


def get_collections():

    collection_list = []

    collections_spreadsheet_id = os.environ['COLLECTIONS_SPREADSHEET_ID']

    collections_workbook = gc.open_by_key(collections_spreadsheet_id)
    collections_ws = collections_workbook.worksheet("OPS")
    collection_table = collections_ws.get_all_values()

    col_index = 1
    for index, col in enumerate(collection_table[0]):
        if col == 'Forge Tig Config':
            col_index = index
            break
    
    for index, row in enumerate(collection_table[1:]):
        if row[col_index] == 'X':
            collection_list.append(row[0])

    return collection_list


# Define a custom exception for retries
class RetryError(Exception):
    pass

# Retry decorator to handle exceptions and implement backoff
@retry(wait_exponential_multiplier=1000, wait_exponential_max=30000, stop_max_attempt_number=7, retry_on_exception=lambda ex: isinstance(ex, RetryError))
def update_sheet(worksheet, cell, data):
    try:
         
        # Update the data in the worksheet
        worksheet.update(data, cell)  # Update cell A1 with your data
        
    except gspread.exceptions.GSpreadException as e:
        print(f"Error: {e}")
        raise RetryError(f"Failed to update. Retrying...")


def get_collection_config(short_name):

    collection_config = DATASET_CONFIG_URL + short_name + '.cfg'
    forge_tig_config_resp = requests.get(collection_config)

    if forge_tig_config_resp.status_code == 200:
        forge_tig_config = forge_tig_config_resp.json()

        return forge_tig_config
 

def create_backfiller(args, logger):

    search = granule_search_from_args(args, logger)
    message_writer = message_writer_from_args(args, logger)

    s3 = S3Reader(logger, args.aws_profile)    # pylint: disable=C0103
    collection = args.collection
    # setup backfiller

#    args.footprint = 'on'
#    args.image = 'on'

    # Check forge configurations before running backfill
#    forge_tig_config = get_collection_config(collection)

#    if forge_tig_config is None:
#        logger.warning("No configuration for collection " + collection + " found.")
#    else:
#        if forge_tig_config.get('footprint'):
#            args.footprint = 'on'
#        imgVariables = forge_tig_config.get('imgVariables')
#        if imgVariables is not None and len(imgVariables) > 0:
#            args.image = 'on'

    safe_log_args(logger, args)

    granule_options = granule_options_from_args(args)

    backfiller = Backfiller(search, message_writer, [],
                            granule_options, logger, args.message_limit, args.cli_execution_id, s3, collection, None)
    
    return backfiller


def get_info(short_name, args):

    mode = cmr.queries.CMR_OPS

    granule_url = cmr.queries.GranuleQuery(
                    mode=mode).provider('POCLOUD').short_name(short_name)._build_url()
    
    headers = {"Authorization": f"Bearer {args.edl_token}"}

    first_granule = requests.get(granule_url, headers=headers, params={
                                'page_size': 1, 'sort_key': 'start_date'}).json()['feed']['entry']
    last_granule = requests.get(granule_url, headers=headers, params={
                                'page_size': 1, 'sort_key': '-start_date'}).json()['feed']['entry']

 #  granule_count = requests.get(granule_url, headers=headers, params={
  #                              'page_size': 0}).headers["CMR-Hits"]

 #   print('granule counts = ' + granule_count)

    time_start = first_granule[0].get("time_start")
    time_end = last_granule[0].get("time_end")

    if (time_end == None):
        print("time_end not found.  This should never happen!")
        now = datetime.now(pytz.timezone('US/Pacific'))
        time_end = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    return dict(time_start = time_start,
                time_end = time_end)


def get_latest_end_date(end_time : str):
    end_date = datetime.strptime(end_time[:7], "%Y-%m")

    current_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    three_months_ago = current_date - relativedelta(months=3)

    if end_date < three_months_ago:
        return end_date
    else:
        return current_date


def gen_date_array(start_time, end_time):
    start_date = datetime.strptime(start_time[:7], "%Y-%m")
    end_date = get_latest_end_date(end_time)

    date_array = []

    current_date = start_date
    while current_date <= end_date:
        date_array.append(current_date.strftime("%Y-%m"))
        # Move to the next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return date_array


def get_total_area_km2(rectangles):
    """Calculate total area in square kilometers for a list of bounding box rectangles.
    
    Args:
        rectangles (list): List of dictionaries containing bounding box coordinates with keys:
            WestBoundingCoordinate, EastBoundingCoordinate, SouthBoundingCoordinate, NorthBoundingCoordinate

    Returns:
        float: Total area in square kilometers
    """
    total_area = 0

    for rect in rectangles:
        west = rect["WestBoundingCoordinate"]
        east = rect["EastBoundingCoordinate"]
        south = rect["SouthBoundingCoordinate"]
        north = rect["NorthBoundingCoordinate"]

        print(f"west: {west}, east: {east}, south: {south}, north: {north}")

        if west == -180 and east == 180:
            # Special case: full longitude span
            lat_fraction = (north - south) / 180.0
            area = EARTH_AREA_KM2 * lat_fraction
            print(f"Rectangle: {rect}, Area (estimated): {area}")
        else:
            if west > east:
                # Crosses antimeridian - create two polygons and union them
                poly1 = box(west, south, 180, north)
                poly2 = box(-180, south, east, north)
                poly = poly1.union(poly2)
                print(f"Antimeridian crossing case: {rect}")
            else:
                # Normal case
                poly = box(west, south, east, north)

            area, _ = geod.geometry_area_perimeter(poly)
            print(f"Rectangle: {rect}, Area: {area}")

        total_area += abs(area)

    # Convert to square kilometers
    total_area_km2 = total_area / 1e6
    print(f"Rectangles: {rectangles}, Total area: {total_area_km2:,.0f} km²")

    return total_area_km2


def get_count_global_bbox(granules):
    """Count granules that have bounding boxes larger than 249,000,000 km².
    
    Args:
        granules (list): List of granule metadata dictionaries containing UMM spatial extent info
        
    Returns:
        int: Count of granules with bounding boxes exceeding the area threshold
    """

    count = 0
    for granule in granules:
        geom = granule['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']

        if 'BoundingRectangles' in geom:
            if get_total_area_km2(geom.get('BoundingRectangles')) > 249000000:
                count += 1

    return count


def update_monthly_counts(backfiller, row_index, month):

    row = [backfiller.search._collection_short_name, month]

    if month in backfiller.monthly_results:
        result = backfiller.monthly_results[month]

        global_bbox_count = get_count_global_bbox(result['granules'])
        row.append(len(result['granules']))
        row.append(result['needs_image'])
        row.append(result['needs_footprint'])
        row.append(global_bbox_count)
        row.append(result['both_footprint_and_bbox'])
    else:
        row.append(0)
        row.append(0)
        row.append(0)
        row.append(0)
        row.append(0)

        print("Month not found in backfiller.  Assuming no granules for this month.")

    now = datetime.now(pytz.timezone('US/Pacific'))
    dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
    row.append(dt_string)

    print("Adding row...")
    print(row)

    try:
        update_sheet(monthly_counts_sheet, "A" + str(row_index), [row])
    except RetryError:
        print("Update failed after multiple retries. You may want to handle this error further.")


def process_one_collection(run):

    args = run['args']
    logger = run['logger']
    row_index = run['row_index']
    month = run['month']

    # run backfiller
    try:
        logger.info("Running backfiller on collection " + args.collection)

        backfiller = create_backfiller(args, logger)

        backfiller.process_granules()

        with lock:
            update_monthly_counts(backfiller, row_index, month)

    except Exception as exc:
        logger.error(f"big error: {exc}")
    except:  # noqa: E722 - to catch ctrl-C
        logger.warning("keyboard interrupt")

    backfiller.log_stats()

    logger.info(f"Finished backfill on {args.collection}: {datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")  # pylint: disable=W1203
    

def fill_monthly_counts(args):
    global monthly_counts_sheet

    collection_list = get_collections()

    print(collection_list)
    print(len(collection_list))

    header = ['Collection Name']
    header.append('Date')
    header.append('Granules')
    header.append('No Image')
    header.append('No Footprint')
    header.append('Global BBox')
    header.append('Both FP & BBox')
    header.append('Updated')

    rows = [header]

    for short_name in collection_list:

        try:
            info = get_info(short_name, args)

            start_time = info['time_start']
            end_time = info['time_end']

            dates = gen_date_array(start_time, end_time)

            print("Collection: " + short_name)
            print(dates)
            print()

            for date in dates:
                row = [short_name, date]
                rows.append(row)
        except IndexError:
            print(f"Warning: Could not add collection {short_name}.  No granules maybe...")

    print("Adding new worksheet: " + worksheet_title)
    monthly_counts_sheet = workbook.add_worksheet(worksheet_title, 1, 8)

    try:
        update_sheet(monthly_counts_sheet, "A1", rows)
    except RetryError:
        print("Update failed after multiple retries. You may want to handle this error further.")


def next_month(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m')

    if date_obj.month == 12:
        next_date = date_obj.replace(year=date_obj.year + 1, month=1)
    else:
        next_date = date_obj.replace(month=date_obj.month + 1)

    return next_date.strftime("%Y-%m")


# def get_granule_count(args):

#     mode = cmr.queries.CMR_OPS

#     granule_url = cmr.queries.GranuleQuery(
#                     mode=mode).provider('POCLOUD').short_name(args.collection)._build_url()
    
#     headers = {"Authorization": f"Bearer {args.edl_token}"}

#     granule_count = requests.get(granule_url, headers=headers, params={
#                                 'page_size': 0}).headers["CMR-Hits"]
    
#     return int(granule_count)


def build_runs(args, logger):

    all_rows = monthly_counts_sheet.get_all_values()

    if not all_rows:
        logger.warning("No data found in the worksheet.")
        return

    runs = []
    for index, row in enumerate(all_rows):

        if row[2] != "":
            continue

        args.collection = row[0]
        args.cli_execution_id = str(uuid.uuid4())

        start_month = row[1]  # Get the start_month value
        args.start_date = f"{start_month}-01T00:00:00Z"
        end_month = next_month(start_month)

        args.end_date = f"{end_month}-01T00:00:00Z"

# TODO: Add column for last granule GPoygon or BBox or both.  Is bbox global or small?
# TODO: Add Expected Granule count and Actual Counted
# TODO: Add a list of granule IDs that failed to easily look them up
        run = dict(
            args = copy.deepcopy(args),
            logger = logger,
            row_index = index+1,
            month = start_month
            )
        runs.append(run)

    random.shuffle(runs)

    return runs


def clear_current_month_counts():

    all_rows = monthly_counts_sheet.get_all_values()

    for index, row in enumerate(all_rows):

        if row[1] == current_month:
            new_row = [row[0], row[1], "", "", "", "", "", ""]
            update_sheet(monthly_counts_sheet, "A" + str(index + 1), [new_row])


def do_count_runs(args, logger):

    if new_monthly_count_sheet:
        logger.info("Filling new worksheet!")
        fill_monthly_counts(args)
    else:
        clear_current_month_counts()

    runs = build_runs(args, logger)

    retry_count = 3

    while len(runs) > 0:
        with ThreadPoolExecutor() as executor:
            executor.map(process_one_collection, runs)

        if retry_count == 0:
            break
        else:
            retry_count -= 1

        runs = build_runs(args, logger)

        logger.info("Retrying monthly counts...")


def do_last_granules_runs(args, logger):

    last_granules_sheet = workbook.worksheet("Last Granules")
    
    collection_list = get_collections()

    print(collection_list)
    print(len(collection_list))

    header = ['Collection Name']
    header.append('Date')
    header.append('Granules')
    header.append('Need Image')
    header.append('Need Footprint')
    header.append('Both FP & BBox')
    header.append('Need DMRPP')
    header.append('Updated')

    rows = [header]

    for short_name in collection_list:

        try:
            args.collection = short_name
            args.cli_execution_id = str(uuid.uuid4())

      #      start_month = row[1]  # Get the start_month value
            args.start_date = f"2024-01-01T00:00:00Z"
       #     end_month = next_month(start_month)

        #    args.end_date = f"{end_month}-01T00:00:00Z"
            backfiller = create_backfiller(args, logger)

            backfiller.process_granules()

         #   results = backfiller.monthly_results['2024-03']

            last_month = list(backfiller.monthly_results.items())[-1]

         #   print(last_month)

         #   print(last_month[1])


        #   print(month)

      #      exit()       

            count_limit = 5

            count = 0
            for granule in reversed(last_month[1]['granules']):

                count += 1

                if count > count_limit:
                    break

                row = [short_name]
        #      print(granule)
                meta = granule['meta']
                umm = granule['umm']
                print(meta)
                row.append(umm['TemporalExtent']['RangeDateTime']['BeginningDateTime'])
                row.append(meta['concept-id'])

                for url in umm['RelatedUrls']:
                    if 'MimeType' in url and url['MimeType'] == 'image/png':
                        image_url = url["URL"]
                    #    match = re.search(r'\.([^\.]+)\.png$', image_url)

                    #    print(image_url)
                    #    var_name = 'Link'
                    #    if match:
                    #        var_name = match.group(1)

                    #    hyperlink_formula = f'=HYPERLINK("{url["URL"]}", "{var_name}")'
                        image_formula = f'=IMAGE("{image_url}", 1)'
                        row.append(image_formula)
                        
             #           last_granules_sheet.update_acell("B2", hyperlink_formula)
             #   row.append(umm['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'])

                rows.append(row)
            break

        except IndexError:
            print(f"Warning: Could not add collection {short_name}.  No granules maybe...")

    try:

        print('update last granules sheet')

        last_granules_sheet.update(rows, value_input_option='USER_ENTERED')
  #      update_sheet(last_granules_sheet, "A1", rows)
        print('done update last granules sheet')
    except RetryError:
        print("Update failed after multiple retries. You may want to handle this error further.")


def bearer_token(env, logger):
    tokens = []
    headers: dict = {'Accept': 'application/json'}
    url: str = f"https://{'uat.' if env == 'uat' else ''}urs.earthdata.nasa.gov/api/users"

    # First just try to get a token that already exists
    try:
        resp = requests.get(url + "/tokens", headers=headers,
                                   auth=requests.auth.HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
        response_content = json.loads(resp.content)

        for x in response_content:
            tokens.append(x['access_token'])

    except Exception as ex:  # noqa E722
        logger.error(ex)
        logger.error("Error getting the token - check user name and password")

    # No tokens exist, try to create one
    if not tokens:
        try:
            resp = requests.post(url + "/token", headers=headers,
                                        auth=requests.auth.HTTPBasicAuth(os.environ['CMR_USER'], os.environ['CMR_PASS']))
            response_content: dict = json.loads(resp.content)
            tokens.append(response_content['access_token'])
        except Exception as ex:  # noqa E722
            logger.error(ex)
            logger.error("Error getting the token - check user name and password")

    # If still no token, then we can't do anything
    if not tokens:
        return None

    return next(iter(tokens))


def main(args=None):
 
    # load args
    args = parse_args(args)

    logger = logger_from_args(args)

    logger.info(f"Started backfill: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    args.edl_token = bearer_token(args.cmr, logger)

    if not args.edl_token:
        logger.error("Could not get bearer token")
        exit(1)

    do_count_runs(args, logger)
  #  do_last_granules_runs(args, logger)

    logger.info(f"Finished all collections: "                                 # pylint: disable=W1203
                f"{datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S %Z')}")


if __name__ == "__main__":
    main()
