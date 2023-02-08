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

    async def __call_api(self, path: str):
        url = self.__base_url.strip("/") + path

        try:
            async with async_timeout.timeout(self.__timeout):
                response = await self.__session.get(url)
                response.raise_for_status()

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
