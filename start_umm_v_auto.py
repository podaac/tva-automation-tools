"""Starter of the Repo Status Updater"""
# pylint: disable=R0801
import argparse

from umm_v_auto.podaac import umm_v_auto_sync



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

if __name__ == "__main__":
    _args = ParseArguments()

    ops_headers = {'Authorization': _args.ops_token}
    uat_headers = {'Authorization': _args.uat_token}

    umm_v_auto_sync.get_l2ss_associations('uat', "PODAAC L2 Cloud Subsetter", uat_headers)

    # Get all the ops collection that are in uat l2ss
    for collection, item in umm_v_auto_sync.uat_collections.items():
        umm_v_auto_sync.get_ops_collection_concept_id('ops', collection, ops_headers)

    for collection, item in umm_v_auto_sync.uat_collections.items():
        umm_v_auto_sync.umm_v_count('uat', item.get('concept_id'),
                    collection, umm_v_auto_sync.uat_collections, uat_headers)

    for collection, item in umm_v_auto_sync.uat_collections.items():

        ops_umm_v = umm_v_auto_sync.ops_collection_name_id[collection].get('umm_v_count')
        uat_umm_v = item.get('umm_v_count')

        if uat_umm_v == 0:
            ops_concept_id = umm_v_auto_sync.ops_collection_name_id[collection].get(
                'concept_id')
            print(f"Sync collection {collection}")
            try:
                umm_v_auto_sync.sync_ops_umm_v_to_uat(ops_concept_id, _args.ops_token, _args.uat_token)
            except Exception as e:  # pylint: disable = broad-exception-caught
                print(e)
    