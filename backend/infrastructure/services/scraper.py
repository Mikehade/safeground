import os
from typing import Optional
from urllib.parse import urlparse

from infrastructure.clients.scraper_api import ScraperAPIClient
# from infrastructure.clients.virus_total import VirusTotalClient

from utils.logger import get_logger

logger = get_logger()


class ScraperService:
    """
    Service layer around ScraperAPIClient for URL scraping.

    Args:
        scraper_client: Configured ScraperAPIClient instance.
        url_scan_client: VirusTotal client for optional pre-scrape URL scanning.
    """

    def __init__(
        self,
        scraper_client: ScraperAPIClient,
        # url_scan_client: VirusTotalClient,
    ) -> None:
        self.scraper_client = scraper_client
        # self.url_scan_client = url_scan_client

    async def scrape_url(
        self,
        url: str,
        scan_url: bool = False,
    ) -> dict:
        """
        Scrape a URL, with optional VirusTotal scan before scraping.

        Args:
            url: The URL to scrape.
            scan_url: If True, scan the URL with VirusTotal before scraping (TODO).

        Returns:
            dict with keys: success (bool), message (str), data (dict).
        """
        try:
            if not self.is_valid_url(url):
                return {
                    "success": False,
                    "message": "Please provide a valid url",
                    "data": {},
                }

            # scan url (TODO)
            # scan_result = await self.url_scan_client.scan_url(url)
            # logger.info(f"URL scan result: {scan_result}")

            results = await self.scraper_client.scrape_url(url=url)
            logger.info(f"Scraped result: {results}")

            return {
                "success": True,
                "message": "Successfully scraped url",
                "data": results,
            }

        except Exception as e:
            logger.error(f"Error occurred while scraping url: {e}")
            return {
                "success": False,
                "message": "Error occurred while scraping url, please try again later",
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False