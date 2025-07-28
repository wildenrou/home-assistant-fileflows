"""The FileFlows integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FileFlowsApiClient, FileFlowsApiError
from .const import CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

SCAN_INTERVAL = timedelta(seconds=30)


class FileFlowsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: FileFlowsApiClient,
    ) -> None:
        """Initialize."""
        self.api_client = api_client
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Only get status since that's the working endpoint
            status_data = await self.api_client.get_status()
            
            _LOGGER.debug("Successfully updated FileFlows data: %s", status_data)
            
            return {
                "status": status_data
            }
            
        except FileFlowsApiError as err:
            _LOGGER.warning("Could not get FileFlows status: %s", err)
            # Return error in status so sensors can handle it
            return {
                "status": {"error": str(err)}
            }
        except Exception as err:
            _LOGGER.error("Error communicating with FileFlows API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up FileFlows from a config entry."""
    _LOGGER.debug("Setting up FileFlows integration")
    
    # Get configuration
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 19200)
    api_key = entry.data.get(CONF_API_KEY)
    
    # Create API client
    api_client = FileFlowsApiClient(
        host=host,
        port=port,
        api_key=api_key,
    )
    
    # Test connection
    try:
        if not await api_client.test_connection():
            await api_client.close()
            raise ConfigEntryNotReady(
                f"Unable to connect to FileFlows at {host}:{port}"
            )
    except Exception as err:
        await api_client.close()
        _LOGGER.error("Failed to connect to FileFlows: %s", err)
        raise ConfigEntryNotReady(
            f"Unable to connect to FileFlows at {host}:{port}: {err}"
        ) from err
    
    # Create coordinator
    coordinator = FileFlowsDataUpdateCoordinator(hass, api_client)
    
    # Fetch initial data so we have data when entities are added
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        await api_client.close()
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady(
            f"Failed to fetch initial data from FileFlows: {err}"
        ) from err
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_client": api_client,
    }
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("FileFlows integration setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading FileFlows integration")
    
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close API client
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["api_client"].close()
        
        _LOGGER.info("FileFlows integration unloaded")
    
    return unload_ok
