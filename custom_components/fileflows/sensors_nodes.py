
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .coordinator import NodeInfoDataUpdateCoordinator
from .const import DOMAIN
from .entity import NodeEntity

async def async_setup_entry(hass, entry, async_add_devices):
    # TODO: Work out how to add new nodes as they appear
    node_info_coordinator = hass.data[DOMAIN][entry.entry_id][NodeInfoDataUpdateCoordinator]
    for node in node_info_coordinator.data:
        async_add_devices([
            StatusNodeSensor(node_info_coordinator, entry, node["Uid"]),
            OperatingSystemNodeSensor(node_info_coordinator, entry, node["Uid"]),
            ArchitectureNodeSensor(node_info_coordinator, entry, node["Uid"])
        ])


class StatusNodeSensor(NodeEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Status"

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_status"

    @property
    def __raw_value(self):
        return int(self._data.get("Status"))

    @property
    def native_value(self) -> str | None:
        if self.__raw_value == 0:
            return "Offline"
        if self.__raw_value == 1:
            return "Idle"
        if self.__raw_value == 2:
            return "Processing"
        if self.__raw_value == 3:
            return "Disabled"
        if self.__raw_value == 4:
            return "Out of Schedule"
        if self.__raw_value == 4:
            return "Version Mismatch"
        return "Unknown"


class OperatingSystemNodeSensor(NodeEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Operating System"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_operating_system"

    @property
    def __raw_value(self):
        return int(self._data.get("OperatingSystem"))

    @property
    def native_value(self) -> str | None:
        if self.__raw_value == 1:
            return "Windows"
        if self.__raw_value == 2:
            return "Linux"
        if self.__raw_value == 3:
            return "Mac"
        if self.__raw_value == 4:
            return "Docker"
        if self.__raw_value == 5:
            return "FreeBSD"
        return "Unknown"

    @property
    def icon(self) -> str | None:
        if self.__raw_value == 1:
            return "mdi:microsoft-windows"
        if self.__raw_value == 2:
            return "mdi:linux"
        if self.__raw_value == 3:
            return "mdi:apple"
        return "mdi:desktop-classic"


class ArchitectureNodeSensor(NodeEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Architecture"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_architecture"

    @property
    def __raw_value(self):
        return int(self._data.get("Architecture"))

    @property
    def native_value(self) -> str | None:
        if self.__raw_value == 1:
            return "x86"
        if self.__raw_value == 2:
            return "x64"
        if self.__raw_value == 3:
            return "Arm32"
        if self.__raw_value == 4:
            return "Arm64"
        return "Unknown"

    @property
    def icon(self) -> str | None:
        if self.__raw_value == 1:
            return "mdi:cpu-32-bit"
        if self.__raw_value == 2:
            return "mdi:cpu-64-bit"
        if self.__raw_value == 3:
            return "mdi:cpu-32-bit"
        if self.__raw_value == 4:
            return "mdi:cpu-64-bit"
        return "mdi:desktop-classic"
