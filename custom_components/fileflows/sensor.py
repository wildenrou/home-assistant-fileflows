
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor.const import SensorDeviceClass

from .coordinator import SystemInfoDataUpdateCoordinator
from .const import DOMAIN, NAME

async def async_setup_entry(hass, entry, async_add_devices):
    system_info_coordinator = hass.data[DOMAIN][entry.entry_id][SystemInfoDataUpdateCoordinator]
    async_add_devices([
        CpuUsageSensor(system_info_coordinator, entry),
        MemoryUsageSensor(system_info_coordinator, entry)
    ])

class CpuUsageSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"{NAME} Server", # TODO: Add config name
            "manufacturer": NAME,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }

    @property
    def unique_id(self):
        return f"{self._config_entry.entry_id}_server_cpu_usage"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device_info.get('name')} CPU Usage"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return int(self.coordinator.data.get("CpuUsage"))

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:memory"

    @property
    def native_unit_of_measurement(self) -> str | None:
        return PERCENTAGE

    @property
    def native_precision(self) -> int | None:
        return 0


class MemoryUsageSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"{NAME} Server", # TODO: Add config name
            "manufacturer": NAME,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }

    @property
    def unique_id(self):
        return f"{self._config_entry.entry_id}_server_memory_usage"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.device_info.get('name')} Memory Usage"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return int(self.coordinator.data.get("MemoryUsage"))

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:memory"

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "B"

    @property
    def suggested_unit_of_measurement(self) -> str | None:
        return "MB"

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.DATA_SIZE
