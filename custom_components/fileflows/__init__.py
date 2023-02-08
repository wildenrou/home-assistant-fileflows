import asyncio
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_TIMEOUT, CONF_SCAN_INTERVAL
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.fileflows.coordinator import SystemInfoDataUpdateCoordinator

from .api import FileFlowsApiClient
from .const import DOMAIN, PLATFORMS


async def async_setup(hass: HomeAssistant, config):
    """Set up this integration using YAML is not supported."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    scan_interval = int(entry.data.get(CONF_SCAN_INTERVAL))
    session = async_get_clientsession(hass)
    client = FileFlowsApiClient(entry.data.get(CONF_URL), int(entry.data.get(CONF_TIMEOUT)), session)

    system_info_coordinator = SystemInfoDataUpdateCoordinator(hass, client, scan_interval)
    await system_info_coordinator.async_refresh()

    if not system_info_coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        SystemInfoDataUpdateCoordinator: system_info_coordinator
    }

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
