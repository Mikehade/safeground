import os
import asyncio
from typing import Dict, Any
from urllib.parse import urlparse

from infrastructure.clients.serp import SerpAPIClient

from utils.logger import get_logger

logger = get_logger()

class SearchService:
    """ 
    Search service to interface with the serp api client for searching 

    Args
        search_client: the search client which is serp api for now
    """

    def __init__(
        self,
        search_client: SerpAPIClient,
    ):
        self.search_client = search_client

    async def search_content(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
            Search for a particular content online using a query

        Args:
            query: the query that we want to search on

        """
        try:
            # validate url
            # is_valid = self.is_valid_url(url)
            # if not is_valid:
            #     return {
            #         "success": False, 
            #         "message": "Please provide a valid url", 
            #         "data": {}
            #     }

            # scrape url
            results = self.search_client.search(
                query=query, 
                allow_multiple=True
            )
            logger.info(f"Search Result: {results}")
        
            return {
                "success": True, 
                "message": "Successfully searched content", 
                "data": results
            }
                
        except Exception as e:
            logger.error(f"\n Error occured searching content: {e} \n")
            return {
                "success": False, 
                "message": "Error occured while searching cotent, please try again later", 
            }

    # helper methods
    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False