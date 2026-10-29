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
                        help='launchpad token for uat',
                        required=False,
                        metavar='')

    parser.add_argument('-ot', '--ops_token',
                        help='launchpad token for ops',
                        required=False,
                        metavar='')

    args = parser.parse_args()
    return args


def sync_association(url_prefix, service_concept_id, headers, current_association, new_association, timeout=60):

    headers["Content-type"] = "application/json"

    print("CMR url: ", url_prefix)
    print("Chain service concept id (associations modified on this UMM-S): ", service_concept_id)
    print("Current chain associations (%d): %s" % (len(current_association), sorted(current_association)))
    print("Target chain associations (%d): %s" % (len(new_association), sorted(new_association)))

    if sorted(current_association) != sorted(new_association):
        add = list(set(new_association) - set(current_association))
        remove = list(set(current_association) - set(new_association))

        print("Concept ids to add (%d) to %s on %s: %s" % (len(add), service_concept_id, url_prefix, sorted(add)))
        print("Concept ids to remove (%d) from %s on %s: %s" % (len(remove), service_concept_id, url_prefix, sorted(remove)))

        """
        for assoc_concept_id in add:
            resp = create_assoc.add_association(url_prefix, service_concept_id, assoc_concept_id, headers, timeout=timeout)
            if resp.status_code != 200:
                print(resp.content)
                print("Failed add association: concept_id being associated may not be valid: %s", assoc_concept_id)
            else:
                print("Succesfully add association: concept_id: ", assoc_concept_id)

        for assoc_concept_id in remove:
            resp = create_assoc.remove_association(url_prefix, service_concept_id, assoc_concept_id, headers, timeout=timeout)
            if resp.status_code != 200:
                print("Failed remove association: concept_id being associated may not be valid: %s", assoc_concept_id)
            else:
                print("Succesfully removed association: concept_id: ", assoc_concept_id)
        """
    else:
        print("All association is the same")


if __name__ == '__main__':

    args = parse_args()

    ops_headers = {'Accept': 'application/json', 'Authorization': args.ops_token}
    uat_headers = {'Accept': 'application/json', 'Authorization': args.uat_token}

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

    for env_name, service_ids, collections in (
            ("UAT", {"l2ss": uat_l2ss_service_concept_id, "concise": uat_concise_service_concept_id, "chain": uat_l2ss_concise_chain_concept_id},
             {"l2ss": uat_l2ss_collections, "concise": uat_concise_collections, "chain": uat_l2ss_concise_chain_collections}),
            ("OPS", {"l2ss": ops_l2ss_service_concept_id, "concise": ops_concise_service_concept_id, "chain": ops_l2ss_concise_chain_concept_id},
             {"l2ss": ops_l2ss_collections, "concise": ops_concise_collections, "chain": ops_l2ss_concise_chain_collections})):
        print("DEBUG %s service concept ids: %s" % (env_name, service_ids))
        for key, value in collections.items():
            print("DEBUG %s %s (%s) associated collections: %s" % (env_name, key, service_ids[key], "None (CMR query failed)" if value is None else "%d" % len(value)))

    print("DEBUG UAT in l2ss but not concise: ", sorted(set(uat_l2ss_collections) - set(uat_concise_collections)))
    print("DEBUG UAT in concise but not l2ss: ", sorted(set(uat_concise_collections) - set(uat_l2ss_collections)))
    print("DEBUG OPS in l2ss but not concise: ", sorted(set(ops_l2ss_collections) - set(ops_concise_collections)))
    print("DEBUG OPS in concise but not l2ss: ", sorted(set(ops_concise_collections) - set(ops_l2ss_collections)))

    print("Sync UAT associations ..........")
    sync_association("https://cmr.uat.earthdata.nasa.gov", uat_l2ss_concise_chain_concept_id, uat_headers, uat_l2ss_concise_chain_collections, uat_in_both_service)

    print("Sync OPS associations ..........")
    sync_association("https://cmr.earthdata.nasa.gov", ops_l2ss_concise_chain_concept_id, ops_headers, ops_l2ss_concise_chain_collections, ops_in_both_service)