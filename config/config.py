"""Config data"""
# pylint: disable=R0903


class Config():
    """Config data"""

    # Misc
    TimeFormat:str = "%Y-%m-%d_-_%H-%M-%S"

    # Launchpad Tokens
    LaunchpadToken_OPS = ""
    LaunchpadToken_UAT = ""

    # API bases
    AWS_base = ""
    CMR_base_OPS = "https://cmr.earthdata.nasa.gov"
    CMR_base_UAT = "https://cmr.uat.earthdata.nasa.gov"
    Harmony_base_OPS = "https://harmony.earthdata.nasa.gov"
    Harmony_base_UAT = "https://harmony.uat.earthdata.nasa.gov"
