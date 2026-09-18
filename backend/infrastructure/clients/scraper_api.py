"""
ScraperAPI Client Module

Async client for the ScraperAPI synchronous scraping endpoint.
Drop-in replacement for ScrapingBeeClient — same return shape throughout.
"""

import asyncio
from typing import Dict, Optional, Any
from enum import Enum
from bs4 import BeautifulSoup

import aiohttp
from aiohttp import ClientTimeout, ClientError


class OutputFormat(str, Enum):
    """Supported output formats."""
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"


class ProxyType(str, Enum):
    """Available proxy types."""
    ROTATING = "rotating"
    PREMIUM = "premium"


class ScraperAPIClient:
    """
    Asynchronous client for the ScraperAPI scraping endpoint.

    Wraps https://api.scraperapi.com with the same interface and return
    shape as the former ScrapingBeeClient so no downstream code changes.

    Attributes:
        api_key (str): ScraperAPI key for authentication.
        base_url (str): Base URL for the ScraperAPI endpoint.
        default_timeout (int): Default request timeout in seconds.
        session (Optional[aiohttp.ClientSession]): Reusable HTTP session.

    Example:
        >>> client = ScraperAPIClient(api_key="your-key", default_timeout=70)
        >>> result = await client.scrape_url("https://example.com")
        >>> print(result["content"])
    """

    def __init__(
        self,
        api_key: str,
        default_timeout: int = 70,
        base_url: str = "https://api.scraperapi.com",
    ) -> None:
        """
        Initialise the ScraperAPI client.

        Args:
            api_key: Your ScraperAPI key (required).
            default_timeout: Timeout in seconds (default: 70 — ScraperAPI's recommended value).
            base_url: ScraperAPI endpoint (default: official endpoint).

        Raises:
            ValueError: If api_key is empty or not a string.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        self.api_key: str = api_key
        self.base_url: str = base_url
        self.default_timeout: int = default_timeout
        self.session: Optional[aiohttp.ClientSession] = None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "ScraperAPIClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def _ensure_session(self) -> None:
        """Create an aiohttp session if one does not exist."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        """
        Close the HTTP session.

        Call this when you are done with the client to release resources.
        Not needed when using the client as an async context manager.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape_url(
        self,
        url: str,
        *,
        timeout: Optional[int] = None,
        render_js: bool = True,
        dynamic_proxy: bool = False,
        proxy_type: ProxyType = ProxyType.ROTATING,
        country_code: Optional[str] = None,
        ai_summary: bool = False,          # kept for interface compatibility; always ignored
        output_format: OutputFormat = OutputFormat.TEXT,
        block_ads: bool = False,           # no ScraperAPI equivalent; accepted and ignored
        block_resources: bool = True,      # no ScraperAPI equivalent; accepted and ignored
        wait: int = 0,
        wait_for: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Scrape a URL via the ScraperAPI endpoint.

        The return shape is identical to the former ScrapingBeeClient so
        all callers (RealTimeDataScraper, ScraperService, etc.) work
        without modification.

        Args:
            url: Target URL to scrape.
            timeout: Per-request timeout in seconds. Falls back to default_timeout.
            render_js: Render JavaScript before returning content (costs extra credits).
            dynamic_proxy: Enable premium proxy pool when proxy_type=PREMIUM.
            proxy_type: ROTATING (default) or PREMIUM.
            country_code: ISO 3166-1 alpha-2 country code for geo-targeting (e.g. "us").
            ai_summary: Accepted for interface compatibility. ScraperAPI has no AI summary
                        feature; this parameter is silently ignored and ai_summary in the
                        response is always an empty string.
            output_format: TEXT (default), HTML, MARKDOWN, or JSON.
            block_ads: Accepted for interface compatibility; no ScraperAPI equivalent.
            block_resources: Accepted for interface compatibility; no ScraperAPI equivalent.
            wait: Additional wait in milliseconds before returning (requires render_js=True).
            wait_for: CSS selector to wait for before returning (requires render_js=True).
            custom_headers: Headers to forward to the target site.
            additional_params: Any extra ScraperAPI query parameters.

        Returns:
            Dict[str, Any]:
                Success::

                    {
                        "success": True,
                        "content": str,
                        "ai_summary": "",        # always empty — ScraperAPI has no AI summary
                        "status_code": int,
                        "url": str,
                        "credits_used": str,     # from sa-credit-cost response header
                        "output_format": str,
                    }

                Error::

                    {
                        "success": False,
                        "error": str,
                        "error_type": str,       # "validation_error" | "timeout" | "client_error"
                                                 # | "api_error" | "unknown"
                        "url": str,
                        "status_code": int | None,
                        "ai_summary": "",
                    }

        Raises:
            ValueError: If url is empty or not a string (returned as error dict, not raised).
        """
        if not url or not isinstance(url, str):
            return {
                "success": False,
                "error": "URL must be a non-empty string",
                "error_type": "validation_error",
                "url": url,
                "status_code": None,
                "ai_summary": "",
            }

        await self._ensure_session()

        request_timeout = timeout if timeout is not None else self.default_timeout
        params = self._build_params(
            url=url,
            render_js=render_js,
            dynamic_proxy=dynamic_proxy,
            proxy_type=proxy_type,
            country_code=country_code,
            output_format=output_format,
            wait=wait,
            wait_for=wait_for,
            additional_params=additional_params,
        )
        headers = self._build_headers(custom_headers)

        try:
            timeout_config = ClientTimeout(total=request_timeout)

            async with self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=timeout_config,
            ) as response:
                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                credits_used = response.headers.get("sa-credit-cost", "unknown")

                if response.status == 200:
                    return {
                        "success": True,
                        "content": text,
                        "ai_summary": "",       # ScraperAPI has no AI summary feature
                        "status_code": response.status,
                        "url": url,
                        "credits_used": credits_used,
                        "output_format": (
                            output_format.value
                            if isinstance(output_format, OutputFormat)
                            else output_format
                        ),
                        "response_headers": dict(response.headers),
                    }

                return {
                    "success": False,
                    "error": f"API returned status {response.status}: {content[:200]}",
                    "error_type": "api_error",
                    "url": url,
                    "status_code": response.status,
                    "response_content": content,
                    "ai_summary": "",
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Request timed out after {request_timeout} seconds",
                "error_type": "timeout",
                "url": url,
                "status_code": None,
                "timeout_duration": request_timeout,
                "ai_summary": "",
            }

        except ClientError as e:
            return {
                "success": False,
                "error": f"Client error: {e}",
                "error_type": "client_error",
                "url": url,
                "status_code": None,
                "exception": type(e).__name__,
                "ai_summary": "",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {e}",
                "error_type": "unknown",
                "url": url,
                "status_code": None,
                "exception": type(e).__name__,
                "ai_summary": "",
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_params(
        self,
        url: str,
        render_js: bool,
        dynamic_proxy: bool,
        proxy_type: ProxyType,
        country_code: Optional[str],
        output_format: OutputFormat,
        wait: int,
        wait_for: Optional[str],
        additional_params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build query parameters for the ScraperAPI GET request."""
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "url": url,
        }

        # JavaScript rendering
        if render_js:
            params["render"] = "true"

        # Proxy configuration
        if dynamic_proxy and proxy_type == ProxyType.PREMIUM:
            params["premium"] = "true"

        # Geo-targeting
        if country_code:
            params["country_code"] = country_code.lower()

        # Output format
        if output_format == OutputFormat.TEXT:
            params["output_format"] = "txt"
        elif output_format == OutputFormat.MARKDOWN:
            params["output_format"] = "markdown"
        elif output_format == OutputFormat.JSON:
            params["autoparse"] = "true"
        # HTML is the default — no extra parameter needed

        # JS wait options (only meaningful with render=true)
        if wait > 0:
            params["wait"] = str(wait)

        if wait_for:
            params["wait_for_selector"] = wait_for

        if additional_params:
            params.update(additional_params)

        return params

    def _build_headers(
        self,
        custom_headers: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        """Build request headers, forwarding any custom headers to the target site."""
        headers: Dict[str, str] = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # ScraperAPI forwards headers that are passed directly in the request
        if custom_headers:
            headers.update(custom_headers)

        return headers