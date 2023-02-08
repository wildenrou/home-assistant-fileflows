from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .api import _LOGGER, FileFlowsApiClient

class SystemInfoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: FileFlowsApiClient, scan_interval: int) -> None:
        """Initialize."""
        self.__client = client

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan_interval))

    async def _async_update_data(self):
        try:
            return await self.__client.async_get_system_info()
        except Exception as exception:
            raise UpdateFailed() from exception
