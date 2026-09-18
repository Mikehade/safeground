"""
Firecrawl Client Module

Async wrapper around the firecrawl-py SDK.
Drop-in replacement for ScraperAPIClient — same return shape throughout,
so RealTimeDataScraper and ScraperService need zero changes.

Install:
    pip install firecrawl-py
"""

import asyncio
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
from enum import Enum

import warnings

warnings.filterwarnings(
    "ignore",
    message=r'Field name "json".*shadows an attribute in parent "BaseModel"',
    category=UserWarning,
)

from firecrawl import Firecrawl
from utils.logger import get_logger

logger = get_logger()


class OutputFormat(str, Enum):
    """Supported output formats."""
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class FirecrawlClient:
    """
    Async client wrapping the Firecrawl SDK.

    The firecrawl-py SDK is synchronous, so all calls are dispatched to a
    thread-pool executor to keep your async event loop free.

    The return shape is identical to ScraperAPIClient (and the former
    ScrapingBeeClient), so RealTimeDataScraper and ScraperService need
    no changes when swapping providers.

    Attributes:
        api_key (str): Firecrawl API key.
        default_timeout (int): Default request timeout in seconds.
        only_main_content (bool): Strip nav/footer boilerplate by default.
        max_age (int): Cache max-age in milliseconds (default: 2 days).
        _client (Firecrawl): Underlying SDK instance.

    Example:
        >>> client = FirecrawlClient(api_key="fc-your-key")
        >>> result = await client.scrape_url("https://example.com")
        >>> print(result["content"])
        >>>
        >>> # With AI summary
        >>> result = await client.scrape_url(
        ...     "https://example.com",
        ...     ai_summary=True
        ... )
        >>> print(result["ai_summary"])
    """

    def __init__(
        self,
        api_key: str,
        default_timeout: int = 60,
        only_main_content: bool = True,
        max_age: int = 172_800_000,         # 2 days in ms — Firecrawl default
    ) -> None:
        """
        Initialise the Firecrawl client.

        Args:
            api_key: Your Firecrawl API key (required, format: "fc-...").
            default_timeout: Default timeout in seconds (converted to ms internally).
            only_main_content: Strip nav, footer, and boilerplate by default.
            max_age: Return a cached version if fresher than this value in ms.
                     Set to 0 to always fetch fresh content.

        Raises:
            ValueError: If api_key is empty or not a string.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        self.api_key: str = api_key
        self.default_timeout: int = default_timeout
        self.only_main_content: bool = only_main_content
        self.max_age: int = max_age
        self._client: Firecrawl = Firecrawl(api_key=api_key)

    # ------------------------------------------------------------------
    # Context manager support (no persistent session needed for SDK)
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "FirecrawlClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass  # SDK manages its own HTTP session

    async def close(self) -> None:
        """No-op — included for interface parity with ScraperAPIClient."""
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape_url(
        self,
        url: str,
        *,
        timeout: Optional[int] = None,
        render_js: bool = True,                     # Firecrawl always renders JS; accepted for parity
        dynamic_proxy: bool = False,                # no Firecrawl equivalent; accepted and ignored
        proxy_type: str = "rotating",               # no Firecrawl equivalent; accepted and ignored
        country_code: Optional[str] = None,         # no Firecrawl equivalent; accepted and ignored
        ai_summary: bool = False,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        block_ads: bool = False,                    # no Firecrawl equivalent; accepted and ignored
        block_resources: bool = True,               # maps to only_main_content when True
        wait: int = 0,
        wait_for: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        parsers: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Scrape a URL via Firecrawl.

        The return shape is identical to ScraperAPIClient so all callers
        (RealTimeDataScraper, ScraperService) work without modification.

        Args:
            url: Target URL to scrape.
            timeout: Per-request timeout in seconds. Falls back to default_timeout.
            render_js: Accepted for interface parity. Firecrawl always renders JS.
            dynamic_proxy: Accepted for interface parity. No Firecrawl equivalent.
            proxy_type: Accepted for interface parity. No Firecrawl equivalent.
            country_code: Accepted for interface parity. No Firecrawl equivalent.
            ai_summary: When True, includes "summary" in the formats list.
                        Firecrawl returns an LLM-generated summary of the page.
            output_format: MARKDOWN (default), HTML, or JSON.
                           TEXT falls back to MARKDOWN (Firecrawl has no plain-text mode).
            block_ads: Accepted for interface parity. No Firecrawl equivalent.
            block_resources: When True, sets only_main_content=True to strip
                             nav/footer boilerplate (closest Firecrawl equivalent).
            wait: Extra wait in milliseconds before scraping.
            wait_for: CSS selector to wait for before returning.
                      Passed as a wait action if provided.
            custom_headers: Headers forwarded to the target site.
            additional_params: Any extra Firecrawl scrape parameters.
            parsers: Parser config, e.g. [{"type": "pdf", "mode": "auto"}].
                     Defaults to ["pdf"] for automatic PDF handling.

        Returns:
            Dict[str, Any]:
                Success::

                    {
                        "success": True,
                        "content": str,         # markdown, html, or JSON string
                        "ai_summary": str,      # LLM summary if ai_summary=True, else ""
                        "status_code": 200,
                        "url": str,
                        "credits_used": "unknown",  # Firecrawl SDK doesn't expose this
                        "output_format": str,
                    }

                Error::

                    {
                        "success": False,
                        "error": str,
                        "error_type": str,      # "validation_error" | "timeout"
                                                # | "scrape_error" | "unknown"
                        "url": str,
                        "status_code": None,
                        "ai_summary": "",
                    }
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

        request_timeout = timeout if timeout is not None else self.default_timeout

        scrape_params = self._build_params(
            url=url,
            timeout_seconds=request_timeout,
            ai_summary=ai_summary,
            output_format=output_format,
            block_resources=block_resources,
            wait=wait,
            wait_for=wait_for,
            custom_headers=custom_headers,
            parsers=parsers,
            additional_params=additional_params,
        )

        try:
            loop = asyncio.get_event_loop()
            doc = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._client.scrape(url, **scrape_params),
                ),
                timeout=request_timeout + 5,    # small buffer over Firecrawl's own timeout
            )

            content = self._extract_content(doc, output_format)
            summary = self._extract_summary(doc, ai_summary)

            return {
                "success": True,
                "content": content,
                "ai_summary": summary,
                "status_code": 200,
                "url": url,
                "credits_used": "unknown",      # Firecrawl SDK doesn't expose credit cost
                "output_format": output_format.value if isinstance(output_format, OutputFormat) else output_format,
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

        except Exception as e:
            logger.error(f"[FirecrawlClient] scrape_url failed for {url}: {e}")
            return {
                "success": False,
                "error": f"Scrape error: {e}",
                "error_type": "scrape_error",
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
        timeout_seconds: int,
        ai_summary: bool,
        output_format: OutputFormat,
        block_resources: bool,
        wait: int,
        wait_for: Optional[str],
        custom_headers: Optional[Dict[str, str]],
        parsers: Optional[List[Any]],
        additional_params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build keyword arguments for firecrawl-py's scrape() call.

        Note: Firecrawl timeout is in milliseconds.
        """
        # Build formats list
        formats: List[Any] = []

        if output_format == OutputFormat.MARKDOWN or output_format == OutputFormat.TEXT:
            formats.append("markdown")
        elif output_format == OutputFormat.HTML:
            formats.append("html")
        elif output_format == OutputFormat.JSON:
            formats.append({
                "type": "json",
                "prompt": "Extract all meaningful content and data from this page",
            })
        else:
            formats.append("markdown")

        if ai_summary:
            formats.append("summary")

        # Build actions list for wait_for selector
        actions = []
        if wait_for:
            actions.append({"type": "wait", "selector": wait_for})

        params: Dict[str, Any] = {
            "formats": formats,
            "only_main_content": block_resources or self.only_main_content,
            "timeout": timeout_seconds * 1000,      # SDK expects milliseconds
            "max_age": self.max_age,
            "parsers": parsers if parsers is not None else ["pdf"],
        }

        if wait > 0:
            params["wait_for"] = wait

        if actions:
            params["actions"] = actions

        if custom_headers:
            params["headers"] = custom_headers

        if additional_params:
            params.update(additional_params)

        return params

    def _extract_content(self, doc: Any, output_format: OutputFormat) -> str:
        """
        Extract content from a Firecrawl document.

        Supported formats:
        - HTML: returns raw HTML
        - JSON: returns serialized JSON
        - TEXT: returns plain text extracted from HTML or markdown
        - MARKDOWN: returns markdown content

        Falls back gracefully when the requested format is unavailable.
        """

        if doc is None:
            return ""

        if output_format == OutputFormat.HTML:
            return (
                getattr(doc, "html", None)
                or getattr(doc, "markdown", None)
                or ""
            )

        if output_format == OutputFormat.JSON:
            raw = getattr(doc, "json", None)
            if raw is None:
                return ""
            return raw if isinstance(raw, str) else json.dumps(raw)

        if output_format == OutputFormat.TEXT:
            # Prefer HTML -> plain text conversion
            html = getattr(doc, "html", None)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                return soup.get_text(separator="\n", strip=True)

            # Fall back to markdown if HTML is unavailable
            markdown = getattr(doc, "markdown", None)
            if markdown:
                return markdown

            return ""

        # Default: MARKDOWN
        return (
            getattr(doc, "markdown", None)
            or getattr(doc, "html", None)
            or ""
        )

    def _extract_summary(self, doc: Any, ai_enabled: bool) -> str:
        """
        Return the LLM-generated summary from the response if it was requested.
        """
        if not ai_enabled:
            return ""
        return getattr(doc, "summary", None) or ""