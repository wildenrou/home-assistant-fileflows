"""FileFlows sensor platform - Conservative version using only status data."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
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
    
    # Create only sensors based on confirmed status data structure
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
        
        # Get host/port from config
        config_data = config_entry.data
        if "url" in config_data and config_data["url"]:
            from urllib.parse import urlparse
            parsed = urlparse(config_data["url"])
            self._host = parsed.hostname or "unknown"
            self._port = parsed.port or 8585
        else:
            self._host = config_data.get(CONF_HOST, config_data.get("host", "unknown"))
            self._port = config_data.get(CONF_PORT, config_data.get("port", 8585))

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
            and isinstance(self.coordinator.data["status"], dict)
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
        self._attr_native_unit_of_measurement = "files"

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
        
        return {
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
        self._attr_native_unit_of_measurement = "files"

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
        
        return {
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
        self._attr_native_unit_of_measurement = "files"

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
            "description": "Total processing time",
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
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "files"

    @property
    def native_value(self) -> Optional[int]:
        """Return the number of processing files."""
        if not self.available:
            return None
        
        status_data = self.coordinator.data.get("status", {})
        processing_files = status_data.get("processingFiles", [])
        return len(processing_files) if isinstance(processing_files, list) else 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:  
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        status_data = self.coordinator.data.get("status", {})
        processing_files = status_data.get("processingFiles", [])
        
        attributes = {
            "last_updated": self.coordinator.last_update_success_time,
        }
        
        # Add details about processing files (limit to avoid entity size issues)
        if isinstance(processing_files, list) and processing_files:
            # Add current file info (first file only to keep it simple)
            current_file = processing_files[0]
            if isinstance(current_file, dict):
                attributes.update({
                    "current_file_name": current_file.get("name", "Unknown"),
                    "current_file_step": current_file.get("step", "Unknown"),
                    "current_file_percent": current_file.get("stepPercent", 0),
                    "current_file_library": current_file.get("library", "Unknown"),
                    "total_processing_files": len(processing_files),
                })
                
                # Add relative path if available and not too long
                rel_path = current_file.get("relativePath", "")
                if rel_path and len(rel_path) < 100:
                    attributes["current_file_path"] = rel_path
        
        return attributes
