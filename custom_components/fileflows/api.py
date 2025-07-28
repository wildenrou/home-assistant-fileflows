"""FileFlows API client - Updated for working FileFlows instance."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class FileFlowsApiError(Exception):
    """Exception to indicate an API error."""


class FileFlowsApiClient:
    """FileFlows API client."""

    def __init__(
        self,
        host: str,
        port: int = 8585,  # Updated default port based on your setup
        api_key: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.api_key = api_key
        self._session = session
        self._close_session = False

    @property
    def base_url(self) -> str:
        """Return the base URL."""
        return f"http://{self.host}:{self.port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session."""
        if self._session is None:
            # Create session with proper headers
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "Home Assistant FileFlows Integration"}
            )
            self._close_session = True
        return self._session

    async def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make a request to the API."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        headers = kwargs.pop("headers", {})
        
        # Add API key if provided
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Set proper headers for JSON
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        
        _LOGGER.debug("Making request: %s %s", method.upper(), url)
        
        try:
            async with session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                content_type = response.headers.get("content-type", "unknown")
                status = response.status
                
                _LOGGER.debug(
                    "Response: %s -> Status: %s, Content-Type: %s",
                    url,
                    status,
                    content_type
                )
                
                # Read response text first
                text = await response.text()
                
                if status == 404:
                    raise FileFlowsApiError(f"Endpoint not found: {endpoint}")
                
                if status >= 400:
                    raise FileFlowsApiError(
                        f"API error {status}: {text}"
                    )
                
                # Try to parse as JSON regardless of content-type header
                # Some servers don't set the correct content-type
                try:
                    import json
                    data = json.loads(text)
                    _LOGGER.debug("Successfully parsed JSON response")
                    return data
                except json.JSONDecodeError as err:
                    _LOGGER.error(
                        "Failed to parse JSON response. Content-Type: %s, Text: %s",
                        content_type,
                        text[:200]
                    )
                    raise FileFlowsApiError(
                        f"Invalid JSON response from {endpoint}: {err}"
                    ) from err
                            
        except asyncio.TimeoutError as err:
            raise FileFlowsApiError(f"Timeout connecting to {url}") from err
        except aiohttp.ClientError as err:
            raise FileFlowsApiError(f"Error connecting to {url}: {err}") from err

    async def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        return await self._request("GET", "/api/status")

    async def test_connection(self) -> bool:
        """Test the connection to FileFlows."""
        try:
            data = await self.get_status()
            _LOGGER.info("Connection test successful. Server status: %s", data)
            return True
        except FileFlowsApiError as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False

    async def close(self) -> None:
        """Close the session."""
        if self._session and self._close_session:
            await self._session.close()
