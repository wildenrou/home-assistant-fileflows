
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, DATA_BYTES, DATA_MEGABYTES
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory

from .coordinator import NodeInfoDataUpdateCoordinator, SystemInfoDataUpdateCoordinator, LibraryFileStatusDataUpdateCoordinator
from .const import DOMAIN, STATUS_MAP
from .entity import NodeInfoEntity, ServerInfoEntity

async def async_setup_entry(hass, entry, async_add_devices):
    system_info_coordinator = hass.data[DOMAIN][entry.entry_id][SystemInfoDataUpdateCoordinator]
    async_add_devices([
        CpuUsageServerSensor(system_info_coordinator, entry),
        MemoryUsageServerSensor(system_info_coordinator, entry)
    ])

    library_file_status_coordinator = hass.data[DOMAIN][entry.entry_id][LibraryFileStatusDataUpdateCoordinator]
    async_add_devices([
        LibraryFileStatusServerSensor(library_file_status_coordinator, entry, s)
        for s, _ in STATUS_MAP.items()
    ])

    # TODO: Work out how to add new nodes as they appear
    node_info_coordinator = hass.data[DOMAIN][entry.entry_id][NodeInfoDataUpdateCoordinator]
    for node in node_info_coordinator.data:
        async_add_devices([
            OperatingSystemNodeSensor(node_info_coordinator, entry, node["Uid"])
        ])


class CpuUsageServerSensor(ServerInfoEntity, SensorEntity):

    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_precision = 0

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_cpu_usage"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_prefix} CPU Usage"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return int(self.coordinator.data.get("CpuUsage"))


class MemoryUsageServerSensor(ServerInfoEntity, SensorEntity):

    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = DATA_BYTES
    _attr_suggested_unit_of_measurement = DATA_MEGABYTES
    _attr_device_class = SensorDeviceClass.DATA_SIZE

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_memory_usage"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_prefix} Memory Usage"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return int(self.coordinator.data.get("MemoryUsage"))


class LibraryFileStatusServerSensor(ServerInfoEntity, SensorEntity):

    _attr_icon = "mdi:file"

    def __init__(self, coordinator, config_entry, status_id):
        super().__init__(coordinator, config_entry)
        self._status_id = status_id

    @property
    def status_name(self):
        return STATUS_MAP[self._status_id]

    @property
    def unique_id(self):
        clean_name = self.status_name.lower().replace(" ", "_")
        return f"{self._unique_id_prefix}_file_count_{clean_name}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_prefix} File Count - {self.status_name}"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        match = [s for s in self.coordinator.data if s["Status"] == self._status_id]
        if match:
            return int(match[0]["Count"])
        return 0


class OperatingSystemNodeSensor(NodeInfoEntity, SensorEntity):

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_operating_system"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name_prefix} Operating System"

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
