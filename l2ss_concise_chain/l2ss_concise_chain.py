import cmr
import requests
from podaac.umms_updater.util import create_assoc
import argparse
import json

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

    parser.add_argument('-ut', '--uat_token',
                        help='launchpad token file for uat',
                        required=False,
                        metavar='')

    parser.add_argument('-ot', '--ops_token',
                        help='launchpad token file for ops',
                        required=False,
                        metavar='')

    args = parser.parse_args()
    return args


def sync_association(url_prefix, service_concept_id, headers, current_association, new_association, timeout=60):

    headers["Content-type"] = "application/json"

    if sorted(current_association) != sorted(new_association):
        add = list(set(new_association) - set(current_association))
        remove = list(set(current_association) - set(new_association))

        print("Concept ids to add: ", add)
        print("Concept ids to remove: ", remove)

        for assoc_concept_id in add:
            resp = create_assoc.add_association(url_prefix, service_concept_id, assoc_concept_id, headers, timeout=timeout)
            if resp.status_code != 200:
                print("Failed add association: concept_id being associated may not be valid: %s", assoc_concept_id)
            else:
                print("Succesfully add association: concept_id: ", assoc_concept_id)

        for assoc_concept_id in remove:
            resp = create_assoc.remove_association(url_prefix, service_concept_id, assoc_concept_id, headers, timeout=timeout)
            if resp.status_code != 200:
                print("Failed remove association: concept_id being associated may not be valid: %s", assoc_concept_id)
            else:
                print("Succesfully removed association: concept_id: ", assoc_concept_id)

    else:
        print("All association is the same")


if __name__ == '__main__':

    _args = parse_args()

    with open(_args.uat_token) as file:
        uat_token_file = json.load(file)
        uat_token = uat_token_file.get('token')

    with open(_args.ops_token) as file:
        ops_token_file = json.load(file)
        ops_token = uat_token_file.get('token')

    ops_headers = {'Authorization': ops_token}
    uat_headers = {'Authorization': uat_token}

    uat_l2ss_service_concept_id = cmr.queries.ServiceQuery(mode=cmr.queries.CMR_UAT).provider('POCLOUD').name('PODAAC L2 Cloud Subsetter').get()[0].get('concept_id')
    uat_l2ss_collections = create_assoc.current_association(uat_l2ss_service_concept_id, "https://cmr.uat.earthdata.nasa.gov", uat_headers)

    ops_l2ss_service_concept_id = cmr.queries.ServiceQuery().provider('POCLOUD').name('PODAAC L2 Cloud Subsetter').get()[0].get('concept_id')
    ops_l2ss_collections = create_assoc.current_association(ops_l2ss_service_concept_id, "https://cmr.earthdata.nasa.gov", ops_headers)

    uat_concise_service_concept_id = cmr.queries.ServiceQuery(mode=cmr.queries.CMR_UAT).provider('POCLOUD').name('PODAAC Concise').get()[0].get('concept_id')
    uat_concise_collections = create_assoc.current_association(uat_concise_service_concept_id, "https://cmr.uat.earthdata.nasa.gov", uat_headers)

    ops_concise_service_concept_id = cmr.queries.ServiceQuery().provider('POCLOUD').name('PODAAC Concise').get()[0].get('concept_id')
    ops_concise_collections = create_assoc.current_association(ops_concise_service_concept_id, "https://cmr.earthdata.nasa.gov", ops_headers)

    uat_l2ss_concise_chain_concept_id = cmr.queries.ServiceQuery(mode=cmr.queries.CMR_UAT).provider('POCLOUD').name('PODAAC L2SS-py Concise Chain').get()[0].get('concept_id')
    uat_l2ss_concise_chain_collections = create_assoc.current_association(uat_l2ss_concise_chain_concept_id, "https://cmr.uat.earthdata.nasa.gov", uat_headers)

    ops_l2ss_concise_chain_concept_id = cmr.queries.ServiceQuery().provider('POCLOUD').name('PODAAC L2SS-py Concise Chain').get()[0].get('concept_id')
    ops_l2ss_concise_chain_collections = create_assoc.current_association(ops_l2ss_concise_chain_concept_id, "https://cmr.earthdata.nasa.gov", ops_headers)

    uat_in_both_service = list(set(uat_l2ss_collections).intersection(uat_concise_collections))
    ops_in_both_service = list(set(ops_l2ss_collections).intersection(ops_concise_collections))

    print("Sync UAT associations ..........")
    sync_association("https://cmr.uat.earthdata.nasa.gov", uat_l2ss_concise_chain_concept_id, uat_headers, uat_l2ss_concise_chain_collections, uat_in_both_service)

    print("Sync OPS associations ..........")
    sync_association("https://cmr.earthdata.nasa.gov", ops_l2ss_concise_chain_concept_id, ops_headers, ops_l2ss_concise_chain_collections, ops_in_both_service)