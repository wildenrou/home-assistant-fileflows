
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.entity import EntityCategory

from .coordinator import NodeInfoDataUpdateCoordinator
from .const import DOMAIN
from .entity import NodeInfoEntity

async def async_setup_entry(hass, entry, async_add_devices):
    # TODO: Work out how to add new nodes as they appear
    node_info_coordinator = hass.data[DOMAIN][entry.entry_id][NodeInfoDataUpdateCoordinator]
    for node in node_info_coordinator.data:
        async_add_devices([
            FlowRunnersNodeNumber(node_info_coordinator, entry, node["Uid"])
        ])


class FlowRunnersNodeNumber(NodeInfoEntity, NumberEntity):

    _attr_has_entity_name = True
    _attr_name = "Flow Runners"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:file-sync-outline"

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_flow_runners"

    @property
    def native_value(self) -> int | None:
        return int(self._data["FlowRunners"])
