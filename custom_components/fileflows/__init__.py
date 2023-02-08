import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup(hass: HomeAssistant, config):
    """Set up this integration using YAML is not supported."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    return True
