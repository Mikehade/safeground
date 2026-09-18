"""
Web tools for LLM agents — scrape and search.
You will wire your own scraper_service and search_service from Elle.
"""
import logging
from typing import Any, Dict

from app.core.tools.base import BaseTool

from utils.logger import get_logger

logger = get_logger()


class WebTools(BaseTool):
    """
    Tools for web search and scraping operations.

    Args:
        scraper_service: your ScraperService (firecrawl, scrapingbee, etc.)
        search_service: your SearchService (SerpAPI, etc.)
    """

    def __init__(
        self,
        scraper_service,
        search_service,
        enabled_tools: list = None,
        **kwargs,
    ) -> None:
        super().__init__(enabled_tools=enabled_tools, **kwargs)
        self.scraper_service = scraper_service
        self.search_service = search_service

    async def execute(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        method = self.get_tool_method(tool_name)
        if not method:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        try:
            tool_input_with_context = {**tool_input, **self.kwargs}
            result = await method(**tool_input_with_context)
            if isinstance(result, dict):
                return result
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _scrape_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Scrape a URL for content.

        Use this tool when:
        - You need to get details from a specific news article or webpage
        - A search result returned a relevant URL you want to read

        Args:
            url: The URL to scrape

        Returns:
            Dictionary with scraped content
        """
        try:
            response = await self.scraper_service.scrape_url(url)
            return {
                "success": response.get("success", False),
                "data": response.get("data", {}),
                "message": "Successfully scraped URL"
                if response.get("success")
                else "Unable to scrape URL",
            }
        except Exception as e:
            logger.error(f"Error scraping url: {e}", exc_info=True)
            return {"success": False, "data": {}, "message": str(e)}

    async def _search_content(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search the web for content.

        Use this tool when:
        - You need to find recent news about safety issues in an area
        - You want to check for reports of unrest, crime, or incidents

        Args:
            query: Search query (e.g. "police brutality Lekki Lagos 2026")

        Returns:
            Dictionary with search results
        """
        try:
            response = await self.search_service.search_content(query)
            return {
                "success": response.get("success", False),
                "data": response.get("data", {}),
                "message": "Successfully searched"
                if response.get("success")
                else "Unable to search",
            }
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return {"success": False, "data": {}, "message": str(e)}
