import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from utils.logger import get_logger

logger = get_logger()


class RealTimeDataScraper:
    def __init__(self, timeout: int = 10, dli_list_url: str = "", scraper_client=None):
        self.timeout = timeout
        self.scraper_client = scraper_client
        self.dli_list_url = dli_list_url

    async def scrape_text(self, session, key, url) -> tuple[str, Optional[str]]:
        """Scrape a single URL and return (key, text). Falls back to ScrapingBee on failure."""
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                if text:
                    return key, text
                raise ValueError("Empty content")

        except Exception as e:
            logger.warning(f"[{key}] Direct scrape failed: {e}. Trying ScrapingBee...")
            return await self._scrape_with_bee(key, url)

    async def _scrape_with_bee(self, key: str, url: str) -> tuple[str, Optional[str]]:
        """Fallback scrape using ScrapingBee client, returns plain text only."""
        if not self.scraper_client:
            logger.error(f"[{key}] No ScrapingBee client configured.")
            return key, None

        try:

            result = await self.scraper_client.scrape_url(
                url,
                render_js=True,
                ai_summary=False,
                output_format="text",
                block_resources=True,
                block_ads=True,
            )

            # logger.info(f"Scraping bee result: {result}")

            if result.get("success") and result.get("content"):
                logger.info(f"[{key}] ScrapingBee succeeded.")
                # Clean up with BeautifulSoup in case HTML slips through
                content = result["content"]
                if "<html" in content.lower():
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text(separator="\n", strip=True)
                return key, content
            else:
                logger.error(f"[{key}] ScrapingBee failed: {result.get('error')}")
                return key, None

        except Exception as e:
            logger.error(f"[{key}] ScrapingBee exception: {e}")
            return key, None

    async def scrape_all_study_permit_urls(self, url_dict: dict) -> dict:
        """Scrape all URLs in parallel and return a dict { key: scraped_text }."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {"User-Agent": "Mozilla/5.0"}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            tasks = [
                asyncio.create_task(self.scrape_text(session, key, url))
                for key, url in url_dict.items()
            ]
            results = await asyncio.gather(*tasks)

        return {key: text for key, text in results if text is not None}

    async def scrape_all_pgwp_urls(self, url_dict: dict) -> dict:
        """Scrape all URLs in parallel and return a dict { key: scraped_text }."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {"User-Agent": "Mozilla/5.0"}

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            tasks = [
                asyncio.create_task(self.scrape_text(session, key, url))
                for key, url in url_dict.items()
            ]
            results = await asyncio.gather(*tasks)

        return {key: text for key, text in results if text is not None}


    async def fetch_schools_dli_list(self) -> dict:
        """ Fetch latest schools DLI list """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.dli_list_url) as res:
                    res.raise_for_status()
                    return await res.json()
        except aiohttp.ClientResponseError as e:
            print(f"HTTP error: {e.status} - {e.message}")
            return {}
        except aiohttp.ClientError as e:
            print(f"Request error: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {}