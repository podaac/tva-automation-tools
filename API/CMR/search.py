'''CMR API interface module'''
# pylint: disable=E1101
# "E1101: Instance of 'Search' has no 'name' member (no-member)" ==> Enum "Provider" have a "name" member

import datetime
import json
import requests
from dateutil.tz.tz import tzlocal

from enums import Provider
import config.config


# Constants
Conf = config.config.Config
BASE_ENDPOINT = '/search'


class Search():
    '''CMR Search interface class'''

    def GetGranules(
        provider: Provider = Provider.POCUMULUS,
        granule_id: str = '',
        start_after: datetime = None,
        short_name: str = '',
        sort_by: str = '-start_date',
        page_size: int = 2000,
        page_num: int = 1,
        date_range: str = '',
        token: str = None,
        use_ops_base: bool = False,
        logging: bool = True
    ) -> requests.Response:
        '''Function to get the Granule list'''

        if logging:
            print('\r\nGetting Granules from CMR...')

        custom_header = {'Cmr-pretty': 'true'}

        base_url = Conf.CMR_base_OPS if use_ops_base else Conf.CMR_base_UAT
        url = f'{base_url + BASE_ENDPOINT}/granules.umm_json?provider={provider.name}'
        if page_size != '':
            url += f'&page_size={page_size}'
        if page_num != '':
            url += f'&page_num={page_num}'
        if granule_id != '':
            url += f'&granule_ur={granule_id}'
        if short_name != '':
            url += f'&short_name={short_name}'
        if sort_by != '':
            url += f'&sort_key={sort_by}'
        if date_range != '':
            url += f'&temporal={date_range}'
        if start_after is not None:
            start_after.replace(tzinfo=tzlocal())
            url += f'&created_at={start_after.isoformat("T", "seconds")[:19]}'
        if token is not None:
            custom_header['Authorization'] = token

        response = requests.get(
            url=url,
            headers=custom_header,
            allow_redirects=True)

        # This is needed so when the response is saved and other steps reach for the response.text content it won't be empty...
        # Looks like there is a need to access it before saving or it will be saved as empty
        temp_text = response.text
        if logging:
            print(f'Response: {response.status_code}')
            print(f'Request url:\r\n{response.request.url}\r\n')
            if response.status_code != 200:
                print(f'Response text:\r\n{temp_text}\r\n')
        return response


    def GetConcept(
        concept_id: str,
        is_native: bool = False,
        logging: bool = True,
        use_ops_base: bool = False
    ) -> requests.Response:
        '''Function to get the Concept details'''

        if logging:
            print('\r\nGetting Concept from CMR...')
            print(f'Concept Id: {concept_id}')
        base_url = Conf.CMR_base_OPS if use_ops_base else Conf.CMR_base_UAT
        url = f'{base_url + BASE_ENDPOINT}/concepts/{concept_id}'

        if is_native:
            url += '.native'

        custom_header = {'Cmr-pretty': 'true'}

        response = requests.get(
            url=url,
            headers=custom_header,
            allow_redirects=True)

        if logging:
            print(f'Response: {response.status_code}')
            if response.status_code != 200:
                print(f'Response text:\r\n{response.text}\r\n')
                print(f'Request url:\r\n{response.request.url}\r\n')

        return response


    def GetCollections(
        provider: Provider = None,
        short_name: str = None,
        token: str = None,
        has_granules: bool = False,
        page_size: int = 2000,
        logging: bool = True,
        use_ops_base: bool = False,
        timeout: int = 30
    ) -> requests.Response:
        '''Function to get the Collection list'''

        if logging:
            print('\r\nGetting Collections from CMR...')

        base_url = Conf.CMR_base_OPS if use_ops_base else Conf.CMR_base_UAT
        url = f'{base_url + BASE_ENDPOINT}/collections.umm_json?page_size={page_size}'
        custom_header = {'Cmr-pretty': 'true'}

        if provider is not None:
            url += f'&provider={provider.name}'
        if short_name is not None:
            url += f'&ShortName={short_name}'
        if has_granules:
            url += f'&has_granules={has_granules}'
        if token is not None:
            url += f'&token={token}'

        response = requests.get(
            url=url,
            headers=custom_header,
            timeout=timeout)

        if logging:
            print(f'Response: {response.status_code}')
            print(f'Request url:\r\n{response.request.url}\r\n')
            if response.status_code != 200:
                print(f'Response text:\r\n{response.text}\r\n')

        return response


    def GetConceptIdForCollection(
        provider: Provider = None,
        short_name: str = None,
        token: str = None,
        has_granules: bool = False,
        page_size: int = 5,
        logging: bool = True,
        use_ops_base: bool = False,
        timeout: int = 30
    ) -> str:
        '''Function to get the Concept ID for the Collection'''

        if logging:
            print('\r\nGetting Concept ID from CMR request...')

        response = Search.GetCollections(
            provider=provider,
            short_name=short_name,
            token=token,
            has_granules=has_granules,
            page_size=page_size,
            logging=logging,
            use_ops_base=use_ops_base,
            timeout=timeout)

        # if response.status_code != 200:
        #     response = Search.GetCollections(
        #         provider=provider,
        #         short_name=short_name,
        #         token=TokenHandler.GetLaunchpadToken(),
        #         has_granules=has_granules,
        #         page_size=page_size,
        #         logging=logging,
        #         use_ops_base=use_ops_base,
        #         timeout=timeout)
        json_data = json.loads(response.text)
        if logging:
            print(f'Hits: {json_data["hits"]}')
        if 'items' not in json_data.keys() or len(json_data['items']) == 0:
            if logging:
                print(f'url: {response.request.url}')
                print(f'response:\r\n{response.text}')
            return ('UrlGenerationError', response)
        collection_concept_id = json_data['items'][0]['meta']['concept-id']

        return collection_concept_id
