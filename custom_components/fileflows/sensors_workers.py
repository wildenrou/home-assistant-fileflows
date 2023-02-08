
from dateutil import parser

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, DATA_BYTES, DATA_GIGABYTES
from homeassistant.components.sensor.const import SensorDeviceClass

from .coordinator import WorkerInfoDataUpdateCoordinator
from .const import DOMAIN
from .entity import WorkerEntity

async def async_setup_entry(hass, entry, async_add_devices):
    # TODO: Work out how to add new nodes as they appear
    worker_info_coordinator = hass.data[DOMAIN][entry.entry_id][WorkerInfoDataUpdateCoordinator]
    for worker in worker_info_coordinator.data:
        async_add_devices([
            StartedWorkerSensor(worker_info_coordinator, entry, worker["Uid"]),
            CurrentPartWorkerSensor(worker_info_coordinator, entry, worker["Uid"]),
            FileLibraryWorkerSensor(worker_info_coordinator, entry, worker["Uid"]),
            FileOriginalSizeWorkerSensor(worker_info_coordinator, entry, worker["Uid"]),
            FlowWorkerSensor(worker_info_coordinator, entry, worker["Uid"])
        ])


class StartedWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Started"
    _attr_icon = "mdi:clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_started"

    @property
    def native_value(self):
        return parser.parse(self._data.get("StartedAt"))


class CurrentPartWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Current Part"

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_current_part"

    @property
    def native_value(self):
        return self._data.get("CurrentPartName")

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "Part Number": self._data.get("CurrentPart"),
            "Total Parts": self._data.get("TotalParts"),
        }


class CurrentPartProgressWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Current Part Progress"
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_current_part_progress"

    @property
    def native_value(self):
        return self._data.get("CurrentPartPercent")


class FileLibraryWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Library"

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_file_library"

    @property
    def native_value(self):
        return self._data.get("Library", {}).get("Name")


class FilePathWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "File Path"

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_file_path"

    @property
    def native_value(self):
        return self._data.get("LibraryFile", {}).get("RelativePath")


class FileOriginalSizeWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Original File Size"
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = DATA_BYTES
    _attr_suggested_unit_of_measurement = DATA_GIGABYTES

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_file_original_size"

    @property
    def native_value(self):
        return self._data.get("LibraryFile", {}).get("OriginalSize")


class FlowWorkerSensor(WorkerEntity, SensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Flow"

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_flow"

    @property
    def native_value(self):
        return self._data.get("LibraryFile", {}).get("FlowName")
