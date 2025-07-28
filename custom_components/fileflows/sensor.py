"""FileFlows sensor platform."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FileFlows sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Create sensors based on the actual API response structure
    sensors = [
        FileFlowsQueueSensor(coordinator, config_entry),
        FileFlowsProcessingSensor(coordinator, config_entry),
        FileFlowsProcessedSensor(coordinator, config_entry),
        FileFlowsTimeSensor(coordinator, config_entry),
        FileFlowsProcessingFilesSensor(coordinator, config_entry),
    ]
    
    async_add_entities(sensors, update_before_add=True)


class FileFlowsBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for FileFlows sensors."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data.get(CONF_PORT, 8585)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._host}_{self._port}")},
            name=f"FileFlows ({self._host})",
            manufacturer="FileFlows",
            model="FileFlows Server",
            sw_version="Unknown",
            configuration_url=f"http://{self._host}:{self._port}",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "status" in self.coordinator.data
            and "error" not in self.coordinator.data.get("status", {})
        )


class FileFlowsQueueSensor(FileFlowsBaseSensor):
    """Sensor for queue count."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Queue"
        self._attr_unique_id = f"{self._host}_{self._port}_queue"
        self._attr_icon = "mdi:format-list-numbered"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:
        """Return the queue count."""
        if not self.available:
            return None
        
        status_data = self.coordinator.data.get("status", {})
        return status_data.get("queue")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        status_data = self.coordinator.data.get("status", {})
        return {
            "unit": "files",
            "last_updated": self.coordinator.last_update_success_time,
        }


class FileFlowsProcessingSensor(FileFlowsBaseSensor):
    """Sensor for processing count."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Processing"
        self._attr_unique_id = f"{self._host}_{self._port}_processing"
        self._attr_icon = "mdi:cog"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[int]:
        """Return the processing count."""
        if not self.available:
            return None
        
        status_data = self.coordinator.data.get("status", {})
        return status_data.get("processing")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        status_data = self.coordinator.data.get("status", {})
        return {
            "unit": "files",
            "last_updated": self.coordinator.last_update_success_time,
        }


class FileFlowsProcessedSensor(FileFlowsBaseSensor):
    """Sensor for processed count."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Processed"
        self._attr_unique_id = f"{self._host}_{self._port}_processed"
        self._attr_icon = "mdi:check-circle"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> Optional[int]:
        """Return the processed count."""
        if not self.available:
            return None
        
        status_data = self.coordinator.data.get("status", {})
        return status_data.get("processed")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        return {
            "unit": "files",
            "last_updated": self.coordinator.last_update_success_time,
        }


class FileFlowsTimeSensor(FileFlowsBaseSensor):
    """Sensor for processing time."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Processing Time"
        self._attr_unique_id = f"{self._host}_{self._port}_time"
        self._attr_icon = "mdi:clock"

    @property
    def native_value(self) -> Optional[str]:
        """Return the processing time."""
        if not self.available:
            return None
        
        status_data = self.coordinator.data.get("status", {})
        return status_data.get("time")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        return {
            "format": "HH:MM",
            "last_updated": self.coordinator.last_update_success_time,
        }


class FileFlowsProcessingFilesSensor(FileFlowsBaseSensor):
    """Sensor for currently processing files."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Processing Files"
        self._attr_unique_id = f"{self._host}_{self._port}_processing_files"
        self._attr_icon = "mdi:file-cog"

    @property
    def native_value(self) -> Optional[int]:
        """Return the number of processing files."""
        if not self.available:
            return None
        
        status_data = self.coordinator.data.get("status", {})
        processing_files = status_data.get("processingFiles", [])
        return len(processing_files)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        status_data = self.coordinator.data.get("status", {})
        processing_files = status_data.get("processingFiles", [])
        
        attributes = {
            "files": [],
            "last_updated": self.coordinator.last_update_success_time,
        }
        
        # Add details about each processing file
        for i, file_info in enumerate(processing_files):
            file_data = {
                "name": file_info.get("name", "Unknown"),
                "relative_path": file_info.get("relativePath", ""),
                "library": file_info.get("library", ""),
                "step": file_info.get("step", ""),
                "step_percent": file_info.get("stepPercent", 0),
            }
            attributes["files"].append(file_data)
            
            # Also add individual file attributes (for first file)
            if i == 0:
                attributes.update({
                    "current_file": file_data["name"],
                    "current_step": file_data["step"],
                    "current_percent": file_data["step_percent"],
                    "current_library": file_data["library"],
                })
        
        return attributes
