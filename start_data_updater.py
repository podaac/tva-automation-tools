'''Starter of the Repo Status Updater'''
# pylint: disable=R0801
import argparse

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


if __name__ == '__main__':
    args = ParseArguments()
    config.config.Config.LaunchpadToken_OPS = args.ops_token
    config.config.Config.LaunchpadToken_UAT = args.uat_token
    config.config.Config.Github_Token = args.github_token
    config.config.Config.Github_Token_JPL = args.github_jpl_token
    Organizer.Start()
