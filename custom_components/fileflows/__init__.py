import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_TIMEOUT, CONF_SCAN_INTERVAL
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FileFlowsApiClient
from .const import DOMAIN, PLATFORMS
from .coordinator import NodeInfoDataUpdateCoordinator, SystemInfoDataUpdateCoordinator, LibraryFileStatusDataUpdateCoordinator, RunnerInfoDataUpdateCoordinator, VersionDataUpdateCoordinator


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


    hass.data[DOMAIN][entry.entry_id] = {
        SystemInfoDataUpdateCoordinator: SystemInfoDataUpdateCoordinator(hass, client, scan_interval),
        VersionDataUpdateCoordinator: VersionDataUpdateCoordinator(hass, client, scan_interval),
        LibraryFileStatusDataUpdateCoordinator: LibraryFileStatusDataUpdateCoordinator(hass, client, scan_interval),
        NodeInfoDataUpdateCoordinator: NodeInfoDataUpdateCoordinator(hass, client, scan_interval),
        RunnerInfoDataUpdateCoordinator: RunnerInfoDataUpdateCoordinator(hass, client, scan_interval)
    }

    for _, coordinator in hass.data[DOMAIN][entry.entry_id].items():
        await coordinator.async_refresh()
        if not coordinator.last_update_success:
            raise ConfigEntryNotReady

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
