"""API interface Module for CMR Search calls"""
from dateutil.tz.tz import tzlocal
import datetime
import requests
import json

from enums import Provider

import config


# File wide variables
endpoint = "/search"
conf = config.config.Config

class Search():
    """Class for CMR Search API functions"""

    def GetGranules(
        provider:Provider = Provider.POCUMULUS,
        granuleId:str = "",
        startAfter:datetime = None,
        shortName:str = "",
        sortBy:str = "-start_date",
        page_size:int = 2000,
        page_num:int = 1,
        daterange:str = "",
        token:str = None,
        logging:bool = True) -> requests.Response:
        """Function to call the granules endpoint"""

        if logging:
            print(f"\r\nGetting Granules from CMR...")
        
        custom_header = {
            "Cmr-pretty": "true"}

        url = f"{conf.CMR_baseurl + endpoint}/granules.umm_json?provider={provider.name}"
        if page_size != "":
            url += f"&page_size={page_size}"
        if page_num != "":
            url += f"&page_num={page_num}"
        if granuleId != "":
            url += f"&granule_ur={granuleId}"
        if shortName != "":
            url += f"&short_name={shortName}"
        if sortBy != "":
            url += f"&sort_key={sortBy}"
        if daterange != "":
            url += f"&temporal={daterange}"
        if startAfter != None:
            startAfter.replace(tzinfo=tzlocal())
            url += "&created_at={0}".format(startAfter.isoformat("T", "seconds")[:19])
        if token != None:
            custom_header["Authorization"] = token

        response = requests.get(
            url = url,
            headers = custom_header,
            allow_redirects = True)

        # This is needed so when the response is saved and other steps reach for the response.text content it won't be empty...
        # Looks like there is a need to access it before saving or it will be saved as empty
        tempText = response.text
        if logging:
            print(f"Response: {response.status_code}")
            print(f"Request url:\r\n{response.request.url}\r\n")
            if response.status_code != 200:   
                print(f"Response text:\r\n{tempText}\r\n")
        return response


    def GetConcept(
        conceptId:str,
        isNative:bool = False,
        logging:bool = True,
        useOPSbase:bool = False) -> requests.Response:
        """Function to call the concepts endpoint"""
    
        if logging:
            print(f"\r\nGetting Concept from CMR...")
            print(f'Concept Id: {conceptId}')
        baseurl = conf.CMR_OPS_baseurl if useOPSbase else conf.CMR_baseurl
        url = f"{baseurl + endpoint}/concepts/{conceptId}"
        
        if isNative:
            url += ".native"
        
        custom_header = { "Cmr-pretty": "true" }

        response = requests.get(
            url = url,
            headers = custom_header,
            allow_redirects = True)
        
        if logging:
            print(f"Response: {response.status_code}")
            if response.status_code != 200:   
                print(f"Response text:\r\n{response.text}\r\n")
                print(f"Request url:\r\n{response.request.url}\r\n")

        return response

    def GetCollections(
        provider:Provider = None,
        shortName:str = None,
        token:str = None,
        has_granules:bool = False,
        page_size:int = 2000,
        logging:bool = True,
        useOPSbase:bool = False,
        timeout:int = 30) -> requests.Response:
        """Function to call the collections endpoint"""

        if logging:
            print(f"\r\nGetting Collections from CMR...")

        baseurl = conf.CMR_OPS_baseurl if useOPSbase else conf.CMR_baseurl
        url = f"{baseurl + endpoint}/collections.umm_json?page_size={page_size}"
        custom_header = { "Cmr-pretty": "true" }  

        if provider != None:
            url += f"&provider={provider.name}"
        if shortName != None:
            url += f"&ShortName={shortName}"
        if has_granules:
            url += f"&has_granules={has_granules}"
        if token != None:
            url += f"&token={token}"
 
        response = requests.get(
            url = url,
            headers = custom_header,
            timeout = timeout)
        
        if logging:
            print(f"Response: {response.status_code}")
            print(f"Request url:\r\n{response.request.url}\r\n")
            if response.status_code != 200:   
                print(f"Response text:\r\n{response.text}\r\n")
        
        return response


    def GetConceptIdForCollection(
        provider:Provider = None,
        shortName:str = None,
        token:str = None,
        has_granules:bool = False,
        page_size:int = 5,
        logging:bool = True,
        useOPSbase:bool = False,
        timeout:int = 30) -> str:
        """Function to get the concept id for the collection through the colelctions endpoint"""
        
        if logging:
            print(f"\r\nGetting Concept ID from CMR request...")
            
        response = Search.GetCollections(
            provider = provider,
            shortName = shortName,
            token = token,
            has_granules = has_granules,
            page_size = page_size,
            logging = logging,
            useOPSbase = useOPSbase,
            timeout = timeout)
 
        if response.status_code != 200 and TokenHandler.CheckIfTokenNeedsUpdate(response.text):
            response = Search.GetCollections(
                provider = provider,
                shortName = shortName,
                token = TokenHandler.GetLaunchpadToken(),
                has_granules = has_granules,
                page_size = page_size,
                logging = logging,
                useOPSbase = useOPSbase,
                timeout = timeout)
        json_data = json.loads(response.text)
        if logging:
            print(f'Hits: {json_data["hits"]}')
        if 'items' not in json_data.keys() or len(json_data["items"]) == 0:
            if logging:
                print(f'url: {response.request.url}')
                print(f'response:\r\n{response.text}')
            return ('UrlGenerationError', response)
        collectionConceptID = json_data["items"][0]["meta"]["concept-id"]
        
        return collectionConceptID