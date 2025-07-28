"""Conservative FileFlows API client - only uses working endpoints."""
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
    """Conservative FileFlows API client using only verified endpoints."""

    def __init__(
        self,
        host: str,
        port: int = 8585,
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
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=15, connect=10)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "Home Assistant FileFlows Integration"}
            )
            self._close_session = True
        return self._session

    async def _request(self, endpoint: str) -> Dict[str, Any]:
        """Make a request to the API."""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        headers = {}
        
        # Add API key if provided (most installations don't need this)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            _LOGGER.debug("Using API key authentication")
        
        # Set proper headers for JSON
        headers["Accept"] = "application/json"
        
        _LOGGER.debug("Making request to: %s", url)
        
        try:
            async with session.get(url, headers=headers) as response:
                status = response.status
                content_type = response.headers.get("content-type", "unknown")
                
                _LOGGER.debug(
                    "Response from %s: Status=%s, Content-Type=%s",
                    endpoint, status, content_type
                )
                
                if status == 404:
                    raise FileFlowsApiError(f"Endpoint not found: {endpoint}")
                
                if status >= 400:
                    text = await response.text()
                    raise FileFlowsApiError(f"HTTP {status} error: {text[:200]}")
                
                # Read response text
                text = await response.text()
                
                # Only try to parse if it looks like JSON
                if not text.strip():
                    raise FileFlowsApiError(f"Empty response from {endpoint}")
                
                if not (text.strip().startswith('{') or text.strip().startswith('[')):
                    raise FileFlowsApiError(f"Non-JSON response from {endpoint}: {text[:100]}")
                
                # Parse JSON
                try:
                    import json
                    data = json.loads(text)
                    _LOGGER.debug("Successfully parsed JSON from %s", endpoint)
                    return data
                except json.JSONDecodeError as err:
                    _LOGGER.error("JSON parse error from %s: %s", endpoint, err)
                    raise FileFlowsApiError(f"Invalid JSON from {endpoint}: {err}") from err
                            
        except asyncio.TimeoutError as err:
            raise FileFlowsApiError(f"Timeout connecting to {url}") from err
        except aiohttp.ClientError as err:
            raise FileFlowsApiError(f"Connection error to {url}: {err}") from err

    async def get_status(self) -> Dict[str, Any]:
        """Get server status - the only endpoint we know works reliably."""
        return await self._request("/api/status")

    async def test_connection(self) -> bool:
        """Test the connection to FileFlows."""
        try:
            data = await self.get_status()
            _LOGGER.info(
                "Connection test successful. Queue: %s, Processing: %s, Processed: %s", 
                data.get('queue', 'N/A'), 
                data.get('processing', 'N/A'),
                data.get('processed', 'N/A')
            )
            return True
        except FileFlowsApiError as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error in connection test: %s", err)
            return False

    async def close(self) -> None:
        """Close the session if we created it."""
        if self._session and self._close_session:
            try:
                await self._session.close()
            except Exception as err:
                _LOGGER.debug("Error closing session: %s", err)
