""" Github actions python script to sync ops umm v variables to uat umm v"""

from datetime import datetime
import argparse
import json
from tqdm import tqdm
import requests
import cmr



# File wide variables
ops_collections = {}
uat_collections = {}
ops_collection_name_id = {}


def Search(*args, **kwargs):
    """Function to make requests calls"""
    return requests.get(*args, **kwargs).json()


def SearchSource(search_api: str, concept_id: str, **kwargs) -> dict:
    """Function to search source cmr for umm v meta data"""

    source_coll_params = {'concept-id': concept_id, **kwargs}
    try:
        source_coll_meta = Search(
            f"{search_api}/collections.umm_json", params=source_coll_params).get("items")[0]
    except (KeyError, IndexError) as e:  # noqa: F841 pylint: disable = unused-variable
        raise Exception(
            f"ERROR! Source collection was not found in CMR ({source_cmr}) for the input concept-id ({source_coll})")  # noqa: F821
    except json.JSONDecodeError as e:  # noqa: F841
        raise Exception(
            f"ERROR! Source collection metadata could not be accessed from CMR ({source_cmr}) due to http request failure")  # noqa: F821

    if 'associations' in source_coll_meta.get("meta"):
        if 'variables' in source_coll_meta.get("meta").get("associations"):
            source_vars = source_coll_meta.get("meta").get(
                "associations").get("variables")
            if len(source_vars) == 0:
                raise Exception(
                    "ERROR! Source collection does not have any associated variables")
        else:
            raise Exception(
                "ERROR! Source collection does not have any associated variables")
    else:
        raise Exception(
            "ERROR! Source collection metadata does not have any associations")

    def SourceVarsFunc(x):
        return (x, Search(f"{search_api}/variables.umm_json", params={'concept-id': x}).get("items")[0])
    return source_coll_meta, dict(map(SourceVarsFunc, tqdm(source_vars)))


def Ingest(*args, **kwargs):
    """Function to make cmr put calls"""
    return requests.put(*args, **kwargs).json()


def IngestTarget(ingest_api: str, variables: dict, token: str, verbose: bool = True) -> list:
    """Function to ingest umm-v"""

    search_api_variables_endpoint = f"{ingest_api.split('ingest/')[0]}search/variables.umm_json"

    def _ingest(record_data: dict) -> dict:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        try:
            meta, umm = record_data.get("meta"), record_data.get("umm")
            ummvar_native_id = meta.get("native-id")
            response = requests.put(f'{ingest_api}/{ummvar_native_id}', data=json.dumps(umm, allow_nan=False), headers={
                # ;version={ummvar_version}",
                'Content-type': "application/vnd.nasa.cmr.umm+json",
                'Authorization': str(token),
                'Accept': "application/json",
            }).json()
            ummvar_concept_id = response.get("concept-id")
        except json.JSONDecodeError as e:  # # noqa: F841 pylint: disable = unused-variable
            print(
                f"ERROR! {ummvar_native_id} -- TODO: Handle failed requests w/ logic to retry errors that appear transient.")
        except Exception as e:  # Skip exceptions so the previous api repsonses are retained.
            status, errors = f"ERROR! Ingest failed for '{meta.get('concept-id')}'", str(
                "\n\t".join(response.get("errors")))
            raise e
        else:
            status, errors = f"SUCCESS! Ingest succeeded for '{ummvar_concept_id}'", f"{search_api_variables_endpoint}?native-id={ummvar_native_id}"
        finally:
            if verbose:
                print("[{}] {} ({}):\n\t{}".format(
                    timestamp, status, ummvar_native_id, errors))
        return response.copy()

    return list(map(lambda x: _ingest(record_data=variables[x]), tqdm(list(variables))))


def ParseArguments():
    """
    Parses the program arguments
    Returns
    -------
    args
    """

    parser = argparse.ArgumentParser(
        description='Synchronize umm-v between ops and uat',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-ut', '--uat_token',
                        help='launchpad token file for uat',
                        required=True,
                        metavar='')

    parser.add_argument('-ot', '--ops_token',
                        help='launchpad token file for ops',
                        required=True,
                        metavar='')

    args = parser.parse_args()
    return args


def GetOPSCollectionConceptId(env, collection_name, headers):
    """Function to get ops concept it and umm v count from collection name"""

    if env == "ops":
        mode = cmr.queries.CMR_OPS
    else:
        mode = cmr.queries.CMR_UAT

    url = cmr.queries.CollectionQuery(mode=mode).provider(
        'POCLOUD').short_name(collection_name)._build_url()
    collections_query = requests.get(url, headers=headers, params={
                                     'page_size': 2000}).json()['feed']['entry']

    if collection_name not in ops_collection_name_id and len(collections_query) > 0:

        variables = collections_query[0].get(
            "associations").get("variables", [])
        ops_collection_name_id[collection_name] = {
            'concept_id': collections_query[0].get('id'),
            'umm_v_count': len(variables)
        }


def GetL2ssAssociations(env, umm_name, headers):
    """Function to get associated collection for l2ss-py for a env"""

    if env == "ops":
        mode = cmr.queries.CMR_OPS
    else:
        mode = cmr.queries.CMR_UAT

    concept_id = cmr.queries.ServiceQuery(mode=mode).provider(
        'POCLOUD').name(umm_name).get()[0].get('concept_id')
    url = cmr.queries.CollectionQuery(
        mode=mode).service_concept_id(concept_id)._build_url()

    collections_query = requests.get(url, headers=headers, params={
                                     'page_size': 2000}).json()['feed']['entry']
    collections = [(a.get('id'), a.get('short_name'))
                   for a in collections_query]
    collections = sorted(collections, key=lambda tup: tup[1])

    collection_concept_ids = []
    for collection in collections:
        if 'POCLOUD' in collection[0]:
            collection_concept_ids.append(collection[0])

            if env == "uat":
                if collection[1] not in uat_collections:
                    uat_collections[collection[1]] = {
                        'concept_id': collection[0]}

            elif env == "ops":
                if collection[1] not in ops_collections:
                    ops_collections[collection[1]] = {
                        'concept_id': collection[0]}


def UmmVCount(env, collection_concept_id, collection, collections, headers):
    """Function to get the umm-v count of a collection"""

    if env == "ops":
        mode = cmr.queries.CMR_OPS
    else:
        mode = cmr.queries.CMR_UAT

    url = cmr.queries.CollectionQuery(
        mode=mode).concept_id(collection_concept_id)._build_url()
    collections_query = requests.get(url, headers=headers, params={
                                     'page_size': 2000}).json()['feed']['entry'][0]

    variables = collections_query.get("associations").get("variables", [])
    collections[collection]['umm_v_count'] = len(variables)


def SyncOpsUmmVtoUAT(ops_concept_id, token_ops, token_uat):
    """Function that will copy umm-v from ops into uat"""

    # ops concept_id
    target_provider = "POCLOUD"

    # Format hostname strings for the source and target CMR venues ->
    source_venue = "ops"
    target_venue = "uat"
    source_cmr = "cmr.{}earthdata.nasa.gov".format(
        source_venue + "." if source_venue in ['uat', 'sit'] else "")
    target_cmr = "cmr.{}earthdata.nasa.gov".format(
        target_venue + "." if target_venue in ['uat', 'sit'] else "")

    # Request metadata about the collection in the source CMR venue ->
    source_pars = {'token': token_ops}
    source_coll_meta, source_vars = SearchSource(
        search_api=f"https://{source_cmr}/search", concept_id=ops_concept_id, **source_pars)
    try:
        # Request metadata about the collection in the target CMR venue ->
        target_coll_meta = Search(f"https://{target_cmr}/search/collections.umm_json",
                                  params={'ShortName': source_coll_meta.get("umm").get("ShortName"),
                                          'provider': target_provider, },
                                  headers={'Accept': "application/json",
                                           'Authorization': token_uat, }, ).get("items")[0]
        target_coll = target_coll_meta.get("meta").get("concept-id")
    except Exception as e:
        raise e

    # Ingest variables to the target CMR collection/provider/venue and return the list of api responses ->
    return IngestTarget(ingest_api=f"https://{target_cmr}/ingest/collections/{target_coll}/variables", variables=source_vars, token=token_uat)


if __name__ == '__main__':

    _args = ParseArguments()

    ops_headers = {'Authorization': _args.ops_token}
    uat_headers = {'Authorization': _args.uat_token}

    GetL2ssAssociations('uat', "PODAAC L2 Cloud Subsetter", uat_headers)

    # Get all the ops collection that are in uat l2ss
    for collection, item in uat_collections.items():
        GetOPSCollectionConceptId('ops', collection, ops_headers)

    for collection, item in uat_collections.items():
        UmmVCount('uat', item.get('concept_id'), collection, uat_collections, uat_headers)

    for collection, item in uat_collections.items():

        ops_umm_v = ops_collection_name_id[collection].get('umm_v_count')
        uat_umm_v = item.get('umm_v_count')

        if uat_umm_v == 0:
            ops_concept_id = ops_collection_name_id[collection].get(
                'concept_id')
            print(f"Sync collection {collection}")
            try:
                SyncOpsUmmVtoUAT(ops_concept_id, _args.ops_token, _args.uat_token)
            except Exception as e:  # pylint: disable = broad-exception-caught
                print(e)
