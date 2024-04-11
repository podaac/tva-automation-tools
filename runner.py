"""Starter of the Repo Status Updater"""
import argparse

from data_updater.organizer import Organizer
import config.config


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

    parser.add_argument('-gt', '--git_token',
                        help='github token',
                        required=True,
                        metavar='')

    parser.add_argument('-jt', '--git_jpl_token',
                        help='jpl github token',
                        required=True,
                        metavar='')

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = ParseArguments()
    config.config.Config.LaunchpadToken_OPS = args.ops_token
    config.config.Config.LaunchpadToken_UAT = args.uat_token
    config.config.Config.Github_Token = args.git_token
    config.config.Config.Github_Token_JPL = args.git_jpl_token
    Organizer.Start()
    