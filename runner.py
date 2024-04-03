"""Starter of the Repo Status Updater"""
import argparse

from data_updater.organizer import Organizer


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
    args = ParseArguments()
    Organizer.Main(args)
    