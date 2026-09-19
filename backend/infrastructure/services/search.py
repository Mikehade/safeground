import asyncio
from typing import Dict, Any
from urllib.parse import urlparse

from infrastructure.clients.serp import SerpAPIClient

from utils.logger import get_logger

logger = get_logger()

# SerpAPI's SDK is synchronous — cap how long we wait for it
_SEARCH_TIMEOUT = 30  # seconds


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
            # SerpAPI SDK is synchronous — run in a thread so we don't
            # block the event loop (which would stall the NDJSON stream).
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    self.search_client.search,
                    query=query,
                    allow_multiple=True,
                ),
                timeout=_SEARCH_TIMEOUT,
            )
            logger.info(f"Search Result: {results}")

            return {
                "success": True,
                "message": "Successfully searched content",
                "data": results
            }

        except asyncio.TimeoutError:
            logger.warning(f"Search timed out after {_SEARCH_TIMEOUT}s for: {query}")
            return {
                "success": False,
                "message": f"Search timed out after {_SEARCH_TIMEOUT}s",
            }

        except Exception as e:
            logger.error(f"\n Error occured searching content: {e} \n")
            return {
                "success": False,
                "message": "Error occured while searching content, please try again later",
            }

    # helper methods
    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False