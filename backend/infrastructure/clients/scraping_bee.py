"""
ScrapingBee API Client Module

This module provides an asynchronous client for interacting with the ScrapingBee API,
handling web scraping with features like proxy rotation, AI-powered extraction, and
multiple output formats.
"""

import asyncio
from typing import Dict, Optional, Any, Literal
from enum import Enum
import aiohttp
from aiohttp import ClientTimeout, ClientError


class OutputFormat(str, Enum):
    """Supported output formats for scraped content."""
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"


class ProxyType(str, Enum):
    """Available proxy types."""
    ROTATING = "rotating"
    PREMIUM = "premium"
    STEALTH = "stealth"


class ScrapingBeeClient:
    """
    Asynchronous client for ScrapingBee API.
    
    This client handles web scraping requests with support for:
    - Configurable timeouts
    - Dynamic proxy rotation
    - AI-powered data extraction
    - Multiple output formats
    - Comprehensive error handling
    
    Attributes:
        api_key (str): ScrapingBee API key for authentication
        base_url (str): Base URL for the ScrapingBee API
        default_timeout (int): Default timeout in seconds for all requests
        session (Optional[aiohttp.ClientSession]): Reusable HTTP session
    
    Example:
        >>> client = ScrapingBeeClient(api_key="your-api-key", default_timeout=30)
        >>> result = await client.scrape_url("https://example.com")
        >>> print(result)
    """
    
    def __init__(
        self,
        api_key: str,
        default_timeout: int = 140,
        base_url: str = "https://app.scrapingbee.com/api/v1"
    ) -> None:
        """
        Initialize the ScrapingBee client.
        
        Args:
            api_key: Your ScrapingBee API key (required)
            default_timeout: Default timeout in seconds for requests (default: 140)
                           Note: ScrapingBee's default timeout is 140 seconds
            base_url: Base URL for the ScrapingBee API (default: official endpoint)
        
        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")
        
        self.api_key: str = api_key
        self.base_url: str = base_url
        self.default_timeout: int = default_timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "ScrapingBeeClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Create aiohttp session if it doesn't exist."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self) -> None:
        """
        Close the HTTP session.
        
        Should be called when done using the client to properly clean up resources.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def scrape_url(
        self,
        url: str,
        *,
        timeout: Optional[int] = None,
        render_js: bool = True,
        dynamic_proxy: bool = False,
        proxy_type: ProxyType = ProxyType.ROTATING,
        country_code: Optional[str] = None,
        ai_summary: bool = False,
        output_format: OutputFormat = OutputFormat.TEXT,
        block_ads: bool = False,
        block_resources: bool = True,
        wait: int = 0,
        wait_for: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scrape a URL using ScrapingBee API.
        
        Args:
            url: The target URL to scrape (required)
            timeout: Request timeout in seconds. If None, uses default_timeout
            render_js: Whether to render JavaScript (default: True)
            dynamic_proxy: Enable dynamic proxy rotation (default: False)
            proxy_type: Type of proxy to use (default: ROTATING)
            country_code: ISO country code for geolocation (e.g., 'us', 'gb', 'de')
            ai_summary: Enable AI-powered summary extraction (default: False)
                       When True, ScrapingBee will generate an AI summary of the page
                       When False, ai_summary key in response will be an empty string
            output_format: Desired output format (default: TEXT)
            block_ads: Block advertisements on the page (default: False)
            block_resources: Block images and CSS (default: True)
            wait: Additional wait time in milliseconds for JS rendering (default: 0)
            wait_for: CSS selector to wait for before returning response
            custom_headers: Dictionary of custom headers to forward
            additional_params: Additional API parameters to include
        
        Returns:
            Dict[str, Any]: Response dictionary with the following structure:
                Success case:
                    {
                        'success': True,
                        'content': str,  # Scraped content
                        'ai_summary': str,  # AI summary if enabled, empty string otherwise
                        'status_code': int,
                        'url': str,  # Original URL
                        'credits_used': int,  # API credits consumed (from headers)
                        'output_format': str
                    }
                Error case:
                    {
                        'success': False,
                        'error': str,  # Error message
                        'error_type': str,  # 'timeout', 'client_error', 'server_error', 'unknown'
                        'url': str,
                        'status_code': Optional[int],
                        'ai_summary': ''  # Always empty string on error
                    }
        
        Raises:
            ValueError: If URL is empty or invalid
        
        Example:
            >>> client = ScrapingBeeClient(api_key="your-key")
            >>> 
            >>> # Basic scraping without AI
            >>> result = await client.scrape_url("https://example.com")
            >>> print(result['ai_summary'])  # Will be empty string ""
            >>> 
            >>> # With AI summary enabled
            >>> result = await client.scrape_url(
            ...     "https://example.com",
            ...     ai_summary=True,
            ...     timeout=60,
            ...     output_format=OutputFormat.JSON
            ... )
            >>> print(result['ai_summary'])  # Will contain AI-generated summary
            >>> 
            >>> # With premium proxy and geolocation
            >>> result = await client.scrape_url(
            ...     "https://example.com",
            ...     dynamic_proxy=True,
            ...     proxy_type=ProxyType.PREMIUM,
            ...     country_code="us",
            ...     ai_summary=False  # Explicitly disabled
            ... )
            >>> print(result['ai_summary'])  # Will be empty string ""
        """
        # Validate input
        if not url or not isinstance(url, str):
            return {
                'success': False,
                'error': 'URL must be a non-empty string',
                'error_type': 'validation_error',
                'url': url,
                'status_code': None,
                'ai_summary': ''  # Always empty on error
            }
        
        # Ensure session exists
        await self._ensure_session()
        
        # Use provided timeout or fall back to default
        request_timeout = timeout if timeout is not None else self.default_timeout
        
        # Build request parameters
        params = self._build_request_params(
            url=url,
            render_js=render_js,
            dynamic_proxy=dynamic_proxy,
            proxy_type=proxy_type,
            country_code=country_code,
            ai_summary=ai_summary,
            output_format=output_format,
            block_ads=block_ads,
            block_resources=block_resources,
            wait=wait,
            wait_for=wait_for,
            additional_params=additional_params
        )
        
        # Build headers
        headers = self._build_headers(custom_headers)
        
        try:
            # Create timeout configuration
            timeout_config = ClientTimeout(total=request_timeout)
            
            # Make the API request
            async with self.session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=timeout_config
            ) as response:
                # Read response content
                content = await response.text()
                
                # Extract credits used from response headers
                credits_used = response.headers.get('Spb-Cost', 'unknown')
                
                # Extract AI summary from response headers if available
                # ScrapingBee returns AI-extracted data in the response body or headers
                extracted_ai_summary = self._extract_ai_summary(
                    response=response,
                    content=content,
                    ai_enabled=ai_summary
                )
                
                # Check if request was successful
                if response.status == 200:
                    return {
                        'success': True,
                        'content': content,
                        'ai_summary': extracted_ai_summary,
                        'status_code': response.status,
                        'url': url,
                        'credits_used': credits_used,
                        'output_format': output_format.value if not isinstance(output_format, str) else output_format,
                        'response_headers': dict(response.headers)
                    }
                else:
                    # Handle API errors
                    return {
                        'success': False,
                        'error': f'API returned status {response.status}: {content}',
                        'error_type': 'api_error',
                        'url': url,
                        'status_code': response.status,
                        'response_content': content,
                        'ai_summary': ''  # Empty on error
                    }
        
        except asyncio.TimeoutError:
            # Handle timeout specifically
            return {
                'success': False,
                'error': f'Request timed out after {request_timeout} seconds',
                'error_type': 'timeout',
                'url': url,
                'status_code': None,
                'timeout_duration': request_timeout,
                'ai_summary': ''  # Empty on error
            }
        
        except ClientError as e:
            # Handle aiohttp client errors (connection errors, etc.)
            return {
                'success': False,
                'error': f'Client error: {str(e)}',
                'error_type': 'client_error',
                'url': url,
                'status_code': None,
                'exception': type(e).__name__,
                'ai_summary': ''  # Empty on error
            }
        
        except Exception as e:
            # Handle any other unexpected errors
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'unknown',
                'url': url,
                'status_code': None,
                'exception': type(e).__name__,
                'ai_summary': ''  # Empty on error
            }
    
    def _build_request_params(
        self,
        url: str,
        render_js: bool,
        dynamic_proxy: bool,
        proxy_type: ProxyType,
        country_code: Optional[str],
        ai_summary: bool,
        output_format: OutputFormat,
        block_ads: bool,
        block_resources: bool,
        wait: int,
        wait_for: Optional[str],
        additional_params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build request parameters for the ScrapingBee API.
        
        Args:
            See scrape_url method for parameter descriptions
        
        Returns:
            Dict[str, Any]: Complete parameter dictionary for API request
        """
        params: Dict[str, Any] = {
            'api_key': self.api_key,
            'url': url,
            'render_js': str(render_js).lower(),
            'block_ads': str(block_ads).lower(),
            'block_resources': str(block_resources).lower()
        }
        
        # Add proxy configuration if dynamic proxy is enabled
        if dynamic_proxy:
            if proxy_type == ProxyType.PREMIUM:
                params['premium_proxy'] = 'true'
            elif proxy_type == ProxyType.STEALTH:
                params['stealth_proxy'] = 'true'
            # ROTATING is the default, no parameter needed
            
            # Add country code if specified
            if country_code:
                params['country_code'] = country_code.lower()
        
        # Add AI summary parameter if enabled
        if ai_summary:
            # Enable AI query for general page summarization
            # Using a general prompt to get a summary of the page
            params['ai_query'] = 'Provide a comprehensive summary of this webpage including key information, main topics, and important details'
        
        # Add output format parameter
        if output_format == OutputFormat.TEXT:
            params['return_page_text'] = 'true'
        elif output_format == OutputFormat.MARKDOWN:
            params['return_page_markdown'] = 'true'
        elif output_format == OutputFormat.JSON:
            params['json_response'] = 'true'
        # HTML is the default format, no parameter needed
        
        # Add wait parameters if specified
        if wait > 0:
            params['wait'] = str(wait)
        
        if wait_for:
            params['wait_for'] = wait_for
        
        # Merge additional parameters if provided
        if additional_params:
            params.update(additional_params)
        
        return params
    
    def _extract_ai_summary(
        self,
        response: aiohttp.ClientResponse,
        content: str,
        ai_enabled: bool
    ) -> str:
        """
        Extract AI summary from the API response.
        
        When AI extraction is enabled, ScrapingBee may return the AI-generated
        summary in different ways depending on the output format:
        - In JSON response format, it's in the response body
        - In other formats, it may be in custom headers
        
        Args:
            response: The aiohttp response object
            content: The response content/body
            ai_enabled: Whether AI summary was requested
        
        Returns:
            str: The extracted AI summary if available and enabled, empty string otherwise
        """
        # If AI summary wasn't requested, always return empty string
        if not ai_enabled:
            return ''
        
        # Try to extract from response headers first
        # ScrapingBee may use custom headers for AI data
        ai_summary_header = response.headers.get('Spb-Ai-Summary', '')
        if ai_summary_header:
            return ai_summary_header
        
        # If json_response was used, try to parse JSON and extract AI data
        # This is a simplified approach - in production you'd want more robust JSON parsing
        if 'json' in content.lower() and content.strip().startswith('{'):
            try:
                import json
                data = json.loads(content)
                # Check for common AI summary fields in the JSON response
                if isinstance(data, dict):
                    # ScrapingBee may return AI results in various keys
                    ai_result = data.get('ai_result', data.get('ai_summary', data.get('summary', '')))
                    if ai_result:
                        return str(ai_result)
            except (json.JSONDecodeError, Exception):
                # If JSON parsing fails, continue to return empty string
                pass
        
        # If we couldn't extract AI summary but it was enabled,
        # it might be embedded in the content itself or not available
        # Return empty string as we couldn't reliably extract it
        return ''
    
    def _build_headers(
        self,
        custom_headers: Optional[Dict[str, str]]
    ) -> Dict[str, str]:
        """
        Build headers for the API request.
        
        Args:
            custom_headers: Optional custom headers to forward to target website
        
        Returns:
            Dict[str, str]: Headers dictionary with properly prefixed custom headers
        """
        headers: Dict[str, str] = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        # Add custom headers with Spb- prefix for forwarding
        if custom_headers:
            for key, value in custom_headers.items():
                # Prefix with Spb- for ScrapingBee to forward to target
                headers[f'Spb-{key}'] = value
        
        return headers