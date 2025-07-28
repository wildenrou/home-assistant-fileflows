"""The FileFlows integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_URL, CONF_TIMEOUT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FileFlowsApiClient, FileFlowsApiError
from .const import CONF_API_KEY, CONF_CONNECTED_LAST_SEEN_TIMESPAN, DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

SCAN_INTERVAL = timedelta(seconds=30)


class FileFlowsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: FileFlowsApiClient,
        scan_interval: timedelta = None,
    ) -> None:
        """Initialize."""
        self.api_client = api_client
        update_interval = scan_interval or SCAN_INTERVAL
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Get comprehensive data from all available endpoints
            data = await self.api_client.get_comprehensive_data()
            
            _LOGGER.debug("Successfully updated FileFlows data. Available keys: %s", 
                         list(data.keys()) if data else "None")
            
            return data
            
        except FileFlowsApiError as err:
            _LOGGER.warning("Could not get FileFlows data: %s", err)
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
    
    # Get configuration - handle both URL and host/port formats
    config_data = entry.data
    
    # Extract host and port from URL if provided, otherwise use direct host/port
    if CONF_URL in config_data and config_data[CONF_URL]:
        from urllib.parse import urlparse
        parsed = urlparse(config_data[CONF_URL])
        host = parsed.hostname
        port = parsed.port or 8585
    else:
        host = config_data.get(CONF_HOST, config_data.get("host"))
        port = config_data.get(CONF_PORT, config_data.get("port", 8585))
    
    if not host:
        _LOGGER.error("No host configured for FileFlows integration")
        return False
    
    api_key = config_data.get(CONF_API_KEY)
    timeout = config_data.get(CONF_TIMEOUT, 10)
    
    _LOGGER.debug("Connecting to FileFlows at %s:%s", host, port)
    
    # Create API client with Home Assistant's session
    session = async_create_clientsession(hass)
    api_client = FileFlowsApiClient(
        host=host,
        port=port,
        api_key=api_key,
        session=session,
    )
    
    # Test connection
    try:
        if not await api_client.test_connection():
            _LOGGER.error("Unable to connect to FileFlows at %s:%s", host, port)
            raise ConfigEntryNotReady(
                f"Unable to connect to FileFlows at {host}:{port}"
            )
    except Exception as err:
        _LOGGER.error("Failed to connect to FileFlows: %s", err)
        raise ConfigEntryNotReady(
            f"Unable to connect to FileFlows at {host}:{port}: {err}"
        ) from err
    
    # Create coordinator with custom scan interval if provided
    scan_interval = timedelta(seconds=config_data.get(CONF_SCAN_INTERVAL, 30))
    coordinator = FileFlowsDataUpdateCoordinator(hass, api_client, scan_interval)
    
    # Fetch initial data so we have data when entities are added
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady(
            f"Failed to fetch initial data from FileFlows: {err}"
        ) from err
    
    # Store coordinator and config
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_client": api_client,
        "config": {
            "host": host,
            "port": port,
            "timeout": timeout,
            "scan_interval": scan_interval.total_seconds(),
            "connected_last_seen_timespan": config_data.get(CONF_CONNECTED_LAST_SEEN_TIMESPAN, DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN),
        }
    }
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    async def pause_processing_service(call):
        """Handle pause processing service call."""
        try:
            result = await api_client.pause_processing()
            if result.get("success", True):
                _LOGGER.info("FileFlows processing paused")
                await coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to pause FileFlows processing: %s", result.get("error"))
        except Exception as err:
            _LOGGER.error("Error pausing FileFlows processing: %s", err)

    async def resume_processing_service(call):
        """Handle resume processing service call."""
        try:
            result = await api_client.resume_processing()
            if result.get("success", True):
                _LOGGER.info("FileFlows processing resumed")
                await coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to resume FileFlows processing: %s", result.get("error"))
        except Exception as err:
            _LOGGER.error("Error resuming FileFlows processing: %s", err)

    async def force_refresh_service(call):
        """Handle force refresh service call."""
        try:
            await coordinator.async_request_refresh()
            _LOGGER.info("FileFlows data refresh requested")
        except Exception as err:
            _LOGGER.error("Error refreshing FileFlows data: %s", err)

    # Register the services
    hass.services.async_register(
        DOMAIN, "pause_processing", pause_processing_service
    )
    hass.services.async_register(
        DOMAIN, "resume_processing", resume_processing_service
    )
    hass.services.async_register(
        DOMAIN, "force_refresh", force_refresh_service
    )
    
    _LOGGER.info("FileFlows integration setup completed for %s:%s", host, port)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading FileFlows integration")
    
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up data (don't close session since it's managed by Home Assistant)
        data = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unregister services if this is the last entry
        if not hass.data[DOMAIN]:  # No more FileFlows integrations
            hass.services.async_remove(DOMAIN, "pause_processing")
            hass.services.async_remove(DOMAIN, "resume_processing")
            hass.services.async_remove(DOMAIN, "force_refresh")
        
        _LOGGER.info("FileFlows integration unloaded")
    
    return unload_ok
