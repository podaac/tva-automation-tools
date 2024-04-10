"""Config data"""
# pylint: disable=R0903


class Config():
    """Config data"""

    # Misc
    TimeFormat:str = "%Y-%m-%d_-_%H:%M:%S"

    # Launchpad Tokens
    LaunchpadToken_OPS = ""
    LaunchpadToken_UAT = ""

    # AWS
    AWS_base = ""

    # CMR
    CMR_base_OPS = "https://cmr.earthdata.nasa.gov"
    CMR_base_UAT = "https://cmr.uat.earthdata.nasa.gov"

    # Cumulus
    Cumulus_base_OPS = ""
    Cumulus_base_UAT = ""

    # Docker
    Docker_base = ""

    # Github
    GitToken = ""
    GitToken_JPL = ""
    Github_base = "https://api.github.com"
    Github_JPL_base = "https://api.github.jpl.nasa.gov"

    # Harmony
    Harmony_base_OPS = "https://harmony.earthdata.nasa.gov"
    Harmony_base_UAT = "https://harmony.uat.earthdata.nasa.gov"

    # PyPi
    PyPi_base = ""
