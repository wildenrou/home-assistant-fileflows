
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, DATA_BYTES, DATA_MEGABYTES
from homeassistant.components.sensor.const import SensorDeviceClass

from .coordinator import SystemInfoDataUpdateCoordinator, LibraryFileStatusDataUpdateCoordinator
from .const import DOMAIN, STATUS_MAP
from .entity import ServerEntity

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


class CpuUsageServerSensor(ServerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "CPU Usage"
    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_precision = 0

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_cpu_usage"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return int(self.coordinator.data.get("CpuUsage"))


class MemoryUsageServerSensor(ServerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Memory Usage"
    _attr_icon = "mdi:memory"
    _attr_native_unit_of_measurement = DATA_BYTES
    _attr_suggested_unit_of_measurement = DATA_MEGABYTES
    _attr_device_class = SensorDeviceClass.DATA_SIZE

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_memory_usage"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return int(self.coordinator.data.get("MemoryUsage"))


class LibraryFileStatusServerSensor(ServerEntity, SensorEntity):

    _attr_has_entity_name = True
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
        return f"File Count - {self.status_name}"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        match = [s for s in self.coordinator.data if s["Status"] == self._status_id]
        if match:
            return int(match[0]["Count"])
        return 0
