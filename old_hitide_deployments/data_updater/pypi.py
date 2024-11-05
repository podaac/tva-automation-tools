'''PyPi module'''
# pylint: disable=C0415, R0903
# C0415 => To avoid circular imports
# R0903 => Need only 1 public method

import re

from data_updater.utils import WebUtils


class PyPi():
    '''Class for PyPi related methods'''

    def GetPyPiVersion(repo_link: str, environment: str) -> str:
        '''Function to get the released version of the Github repository published to PyPi'''

        # Get the link from the PyPi Release method
        from data_updater.distributor import Distributor
        url = Distributor.GeneratePyPiReleaseLink(repo_link, environment)
        result = url
        print(f'result: {result}')
        if 'not found' not in url.lower() and 'does not exists' not in url.lower():
            # Get the page content
            raw_page_content = WebUtils.GetUrl(url)

            # Extract the version from the PyPi page
            pattern = r'<h1\s+class=.package-header__name.>\s+[0-9a-zA-Z.,-]+\s([0-9a-zA-Z.,-]+)\s+<\/h1>'
            mo = re.findall(pattern=pattern, string=raw_page_content)
            if len(mo) > 0:
                result = mo[-1]
            else:
                result = 'No Version number found on the PyPi page!'
        return result
