
from homeassistant.components.update import UpdateEntity

from .coordinator import VersionDataUpdateCoordinator
from .const import DOMAIN, NAME
from .entity import ServerEntity

async def async_setup_entry(hass, entry, async_add_devices):
    version_coordinator = hass.data[DOMAIN][entry.entry_id][VersionDataUpdateCoordinator]
    async_add_devices([
        ServerUpdateEntity(version_coordinator, entry)
    ])


class ServerUpdateEntity(ServerEntity, UpdateEntity):

    _attr_title = NAME
    _attr_release_url = "https://fileflows.com/docs/versions"

    @property
    def latest_version(self):
        return self.coordinator.data.get("latest")

    @property
    def installed_version(self):
        return self.coordinator.data.get("installed")

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}"

