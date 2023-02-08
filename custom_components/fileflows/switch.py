
from typing import Any
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .coordinator import NodeInfoDataUpdateCoordinator
from .const import DOMAIN
from .entity import NodeInfoEntity

async def async_setup_entry(hass, entry, async_add_devices):
    # TODO: Work out how to add new nodes as they appear
    node_info_coordinator = hass.data[DOMAIN][entry.entry_id][NodeInfoDataUpdateCoordinator]
    for node in node_info_coordinator.data:
        async_add_devices([
            EnabledNodeSwitch(node_info_coordinator, entry, node["Uid"])
        ])


class EnabledNodeSwitch(NodeInfoEntity, SwitchEntity):

    _attr_has_entity_name = True
    _attr_name = "Enabled"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_enabled"

    @property
    def is_on(self) -> bool | None:
        return bool(self._data["Enabled"])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_set_state(False)

    async def async_set_state(self, is_enabled: bool) -> None:
        await self.coordinator.client.async_set_node_state(self._node_uid, is_enabled)
        await self.coordinator.async_request_refresh()
