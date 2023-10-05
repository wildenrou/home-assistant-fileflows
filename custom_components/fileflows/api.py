import asyncio
import logging
import aiohttp
import async_timeout

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FileFlowsApiClient:

    def __init__(self, url: str, timeout: int, session: aiohttp.ClientSession) -> None:
        self.__base_url = url
        self.__timeout = timeout
        self.__session = session

    async def async_get_system_version(self) -> str:
        """Gets the version number of FileFlows server."""
        return await self.__call_api("/api/system/version")

    async def async_get_system_info(self) -> dict:
        """Gets the system info from the fileflows server."""
        return await self.__call_api("/api/system/info")

    async def async_get_library_file_status(self) -> dict:
        """Gets the library file status from the fileflows server."""
        return await self.__call_api("/api/library-file/status")

    async def async_get_node_info(self) -> dict:
        """Gets the node info from the fileflows server."""
        return await self.__call_api("/api/node")

    async def async_set_node_state(self, node_uid: str, is_enabled: bool) -> dict:
        """Gets the node info from the fileflows server."""
        return await self.__call_api(f"/api/node/state/{node_uid}?enable={is_enabled}", method="put")

    async def async_get_worker_info(self) -> dict:
        """Gets the worker (referred to as runner in UI) info from the fileflows server."""
        return await self.__call_api("/api/worker")

    async def __call_api(self, path: str, method: str = "get"):
        url = self.__base_url.strip("/") + path

        _LOGGER.debug("Sending request %s to %s", method, url)

        try:
            async with async_timeout.timeout(self.__timeout):
                if method.lower() == "get":
                    response = await self.__session.get(url)
                elif method.lower() == "put":
                    response = await self.__session.put(url)
                else:
                    raise ValueError(f"Unrecognised HTTP method {method}")

                response.raise_for_status()
                _LOGGER.debug("Request to %s successful", url)

                if response.content_type == "text/plain":
                    return await response.text()
                if response.content_type == "application/json":
                    return await response.json()
                raise TypeError(f"Unknown content type {response.content_type} from API")
        except asyncio.TimeoutError as ex:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                ex,
            )
            raise
        except Exception as ex:
            _LOGGER.error(
                "Unknown error calling %s - %s",
                url,
                ex,
            )
            raise
