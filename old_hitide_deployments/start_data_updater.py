'''Starter of the Repo Status Updater'''
# pylint: disable=R0801
import argparse

import json
import boto3

from data_updater.organizer import Organizer
import config.config


def ParseArguments():
    '''
    Parses the program arguments
    Returns
    -------
    args
    '''

    parser = argparse.ArgumentParser(
        description='Collect data from repositories and put it in a spreadsheet',
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

    parser.add_argument('-gt', '--github_token',
                        help='github token',
                        required=True,
                        metavar='')

    parser.add_argument('-jt', '--github_jpl_token',
                        help='jpl github token',
                        required=True,
                        metavar='')

    args = parser.parse_args()
    return args


def list_lambda_function_details():
    # Create a Lambda client
    client = boto3.client('lambda')

    # Initialize an empty list to store function details
    function_details = []

    # Paginate through all the Lambda functions
    paginator = client.get_paginator('list_functions')
    for page in paginator.paginate():
        for function in page['Functions']:
            function_name = function['FunctionName']
            # Get the detailed information for each function
            function_detail = client.get_function(FunctionName=function_name)
            function_details.append(function_detail)
    
if __name__ == '__main__':

#    print('im here')
#    function_details = list_lambda_function_details()
#    for function_detail in function_details:
#        print(json.dumps(function_detail, indent=4))

    args = ParseArguments()
    config.config.Config.LaunchpadToken_OPS = args.ops_token
    config.config.Config.LaunchpadToken_UAT = args.uat_token
    config.config.Config.Github_Token = args.github_token
    config.config.Config.Github_Token_JPL = args.github_jpl_token
    Organizer.Start()
