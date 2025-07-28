"""Enhanced FileFlows API client with additional endpoints."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class FileFlowsApiError(Exception):
    """Exception to indicate an API error."""


class FileFlowsApiClient:
    """Enhanced FileFlows API client with additional endpoints."""

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
                    url, status, content_type
                )
                
                if status == 404:
                    raise FileFlowsApiError(f"Endpoint not found: {endpoint}")
                
                if status >= 400:
                    text = await response.text()
                    raise FileFlowsApiError(f"API error {status}: {text}")
                
                # Read response text first
                text = await response.text()
                
                # Try to parse as JSON
                try:
                    import json
                    data = json.loads(text)
                    _LOGGER.debug("Successfully parsed JSON response from %s", endpoint)
                    return data
                except json.JSONDecodeError as err:
                    _LOGGER.error(
                        "Failed to parse JSON from %s. Text: %s",
                        endpoint, text[:200]
                    )
                    raise FileFlowsApiError(
                        f"Invalid JSON response from {endpoint}: {err}"
                    ) from err
                            
        except asyncio.TimeoutError as err:
            raise FileFlowsApiError(f"Timeout connecting to {url}") from err
        except aiohttp.ClientError as err:
            raise FileFlowsApiError(f"Error connecting to {url}: {err}") from err

    async def get_status(self) -> Dict[str, Any]:
        """Get server status with queue, processing, and file information."""
        return await self._request("GET", "/api/status")

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information including version."""
        endpoints_to_try = [
            "/api/system",
            "/api/system/info", 
            "/api/info",
            "/api/version"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                return await self._request("GET", endpoint)
            except FileFlowsApiError:
                continue
                
        # Return basic info if no endpoint works
        return {"error": "No system info endpoint available"}

    async def get_flows(self) -> Dict[str, Any]:
        """Get available flows."""
        try:
            return await self._request("GET", "/api/flows")
        except FileFlowsApiError:
            return {"flows": [], "error": "Could not get flows"}

    async def get_libraries(self) -> Dict[str, Any]:
        """Get configured libraries."""
        try:
            return await self._request("GET", "/api/libraries")
        except FileFlowsApiError:
            return {"libraries": [], "error": "Could not get libraries"}

    async def get_nodes(self) -> Dict[str, Any]:
        """Get processing nodes information."""
        endpoints_to_try = ["/api/nodes", "/api/workers", "/api/node"]
        
        for endpoint in endpoints_to_try:
            try:
                return await self._request("GET", endpoint)
            except FileFlowsApiError:
                continue
                
        return {"nodes": [], "error": "Could not get nodes"}

    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        endpoints_to_try = [
            "/api/statistics", 
            "/api/stats", 
            "/api/dashboard",
            "/api/dashboard/statistics"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                return await self._request("GET", endpoint)
            except FileFlowsApiError:
                continue
                
        return {"statistics": {}, "error": "Could not get statistics"}

    async def get_settings(self) -> Dict[str, Any]:
        """Get FileFlows settings."""
        try:
            return await self._request("GET", "/api/settings")
        except FileFlowsApiError:
            return {"settings": {}, "error": "Could not get settings"}

    async def get_plugins(self) -> Dict[str, Any]:
        """Get installed plugins."""
        try:
            return await self._request("GET", "/api/plugins")
        except FileFlowsApiError:
            return {"plugins": [], "error": "Could not get plugins"}

    async def get_file_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get file processing history."""
        endpoints_to_try = [
            f"/api/files?limit={limit}",
            f"/api/history?limit={limit}",
            f"/api/file-history?limit={limit}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                return await self._request("GET", endpoint)
            except FileFlowsApiError:
                continue
                
        return {"files": [], "error": "Could not get file history"}

    async def get_log_entries(self, lines: int = 100) -> Dict[str, Any]:
        """Get recent log entries."""
        endpoints_to_try = [
            f"/api/logs?lines={lines}",
            f"/api/log?lines={lines}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                return await self._request("GET", endpoint)
            except FileFlowsApiError:
                continue
                
        return {"logs": [], "error": "Could not get logs"}

    async def pause_processing(self) -> Dict[str, Any]:
        """Pause file processing."""
        try:
            return await self._request("POST", "/api/pause")
        except FileFlowsApiError as err:
            return {"success": False, "error": str(err)}

    async def resume_processing(self) -> Dict[str, Any]:
        """Resume file processing."""
        try:
            return await self._request("POST", "/api/resume")
        except FileFlowsApiError as err:
            return {"success": False, "error": str(err)}

    async def get_comprehensive_data(self) -> Dict[str, Any]:
        """Get all available data from FileFlows in one call."""
        data = {}
        
        # Get status (primary endpoint)
        try:
            data["status"] = await self.get_status()
        except Exception as err:
            _LOGGER.error("Failed to get status: %s", err)
            data["status"] = {"error": str(err)}

        # Get additional data (optional)
        additional_endpoints = [
            ("system_info", self.get_system_info),
            ("flows", self.get_flows),
            ("libraries", self.get_libraries),
            ("nodes", self.get_nodes),
            ("statistics", self.get_statistics),
            ("settings", self.get_settings),
            ("plugins", self.get_plugins),
            ("file_history", lambda: self.get_file_history(5)),  # Limit to 5 recent files
        ]
        
        for key, method in additional_endpoints:
            try:
                result = await method()
                if not result.get("error"):
                    data[key] = result
                else:
                    _LOGGER.debug("Endpoint %s returned error: %s", key, result.get("error"))
            except Exception as err:
                _LOGGER.debug("Failed to get %s: %s", key, err)
        
        return data

    async def test_connection(self) -> bool:
        """Test the connection to FileFlows."""
        try:
            data = await self.get_status()
            _LOGGER.info("Connection test successful. Queue: %s, Processing: %s", 
                        data.get('queue', 'N/A'), data.get('processing', 'N/A'))
            return True
        except FileFlowsApiError as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False

    async def close(self) -> None:
        """Close the session if we created it."""
        if self._session and self._close_session:
            await self._session.close()
