"""Enhanced FileFlows sensor platform with additional sensors."""
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
    
    # Create sensors based on available data
    sensors = [
        # Core status sensors
        FileFlowsQueueSensor(coordinator, config_entry),
        FileFlowsProcessingSensor(coordinator, config_entry),
        FileFlowsProcessedSensor(coordinator, config_entry),
        FileFlowsTimeSensor(coordinator, config_entry),
        FileFlowsProcessingFilesSensor(coordinator, config_entry),
        
        # Additional sensors for enhanced data
        FileFlowsSystemStatusSensor(coordinator, config_entry),
        FileFlowsNodeCountSensor(coordinator, config_entry),
        FileFlowsFlowCountSensor(coordinator, config_entry),
        FileFlowsLibraryCountSensor(coordinator, config_entry),
        FileFlowsPluginCountSensor(coordinator, config_entry),
    ]
    
    async_add_entities(sensors, update_before_add=True)


class FileFlowsBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for FileFlows sensors."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._host = config_entry.data.get(CONF_HOST, config_entry.data.get("host", "unknown"))
        self._port = config_entry.data.get(CONF_PORT, config_entry.data.get("port", 8585))

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        # Try to get version from system_info if available
        version = "Unknown"
        if (self.coordinator.data and 
            "system_info" in self.coordinator.data and 
            "version" in self.coordinator.data["system_info"]):
            version = self.coordinator.data["system_info"]["version"]
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._host}_{self._port}")},
            name=f"FileFlows ({self._host})",
            manufacturer="FileFlows",
            model="FileFlows Server",
            sw_version=version,
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


# Core sensors (existing)
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
        return len(processing_files)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        status_data = self.coordinator.data.get("status", {})
        processing_files = status_data.get("processingFiles", [])
        
        attributes = {"files": []}
        
        # Add details about each processing file (limit to 5 for performance)
        for i, file_info in enumerate(processing_files[:5]):
            file_data = {
                "name": file_info.get("name", "Unknown"),
                "relative_path": file_info.get("relativePath", ""),
                "library": file_info.get("library", ""),
                "step": file_info.get("step", ""),
                "step_percent": file_info.get("stepPercent", 0),
            }
            attributes["files"].append(file_data)
            
            # Add current file attributes (for first file)
            if i == 0:
                attributes.update({
                    "current_file": file_data["name"],
                    "current_step": file_data["step"],
                    "current_percent": file_data["step_percent"],
                    "current_library": file_data["library"],
                })
        
        return attributes


# Enhanced sensors for additional data
class FileFlowsSystemStatusSensor(FileFlowsBaseSensor):
    """Sensor for system status and version."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows System Status"
        self._attr_unique_id = f"{self._host}_{self._port}_system_status"
        self._attr_icon = "mdi:server"

    @property
    def native_value(self) -> Optional[str]:
        """Return the system status."""
        if not self.available:
            return "offline"
        
        # If we have system info, check for specific status
        if "system_info" in self.coordinator.data:
            system_info = self.coordinator.data["system_info"]
            if "error" not in system_info:
                return "online"
        
        return "online"  # If status endpoint works, system is online

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        attributes = {}
        
        # Add system info if available
        if "system_info" in self.coordinator.data:
            system_info = self.coordinator.data["system_info"]
            if "error" not in system_info:
                attributes.update({
                    "version": system_info.get("version", "Unknown"),
                    "build": system_info.get("build", "Unknown"),
                })
        
        return attributes


class FileFlowsNodeCountSensor(FileFlowsBaseSensor):
    """Sensor for number of processing nodes."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Nodes"
        self._attr_unique_id = f"{self._host}_{self._port}_nodes"
        self._attr_icon = "mdi:server-network"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "nodes"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and
            "nodes" in self.coordinator.data and
            "error" not in self.coordinator.data.get("nodes", {})
        )

    @property
    def native_value(self) -> Optional[int]:
        """Return the number of nodes."""
        if not self.available:
            return None
        
        nodes_data = self.coordinator.data.get("nodes", {})
        nodes = nodes_data.get("nodes", nodes_data.get("workers", []))
        return len(nodes) if isinstance(nodes, list) else 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        nodes_data = self.coordinator.data.get("nodes", {})
        nodes = nodes_data.get("nodes", nodes_data.get("workers", []))
        
        if isinstance(nodes, list) and nodes:
            active_nodes = [n for n in nodes if n.get("enabled", True)]
            return {
                "total_nodes": len(nodes),
                "active_nodes": len(active_nodes),
                "nodes": [{"name": n.get("name", "Unknown"), 
                          "enabled": n.get("enabled", True)} for n in nodes[:10]]
            }
        
        return {}


class FileFlowsFlowCountSensor(FileFlowsBaseSensor):
    """Sensor for number of configured flows."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Flows"
        self._attr_unique_id = f"{self._host}_{self._port}_flows"
        self._attr_icon = "mdi:workflow"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "flows"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and
            "flows" in self.coordinator.data and
            "error" not in self.coordinator.data.get("flows", {})
        )

    @property
    def native_value(self) -> Optional[int]:
        """Return the number of flows."""
        if not self.available:
            return None
        
        flows_data = self.coordinator.data.get("flows", {})
        flows = flows_data.get("flows", [])
        return len(flows) if isinstance(flows, list) else 0


class FileFlowsLibraryCountSensor(FileFlowsBaseSensor):
    """Sensor for number of configured libraries."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Libraries"
        self._attr_unique_id = f"{self._host}_{self._port}_libraries"
        self._attr_icon = "mdi:library"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "libraries"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and
            "libraries" in self.coordinator.data and
            "error" not in self.coordinator.data.get("libraries", {})
        )

    @property
    def native_value(self) -> Optional[int]:
        """Return the number of libraries."""
        if not self.available:
            return None
        
        libraries_data = self.coordinator.data.get("libraries", {})
        libraries = libraries_data.get("libraries", [])
        return len(libraries) if isinstance(libraries, list) else 0


class FileFlowsPluginCountSensor(FileFlowsBaseSensor):
    """Sensor for number of installed plugins."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Plugins"
        self._attr_unique_id = f"{self._host}_{self._port}_plugins"
        self._attr_icon = "mdi:puzzle"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "plugins"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available and
            "plugins" in self.coordinator.data and
            "error" not in self.coordinator.data.get("plugins", {})
        )

    @property
    def native_value(self) -> Optional[int]:
        """Return the number of plugins."""
        if not self.available:
            return None
        
        plugins_data = self.coordinator.data.get("plugins", {})
        plugins = plugins_data.get("plugins", [])
        return len(plugins) if isinstance(plugins, list) else 0
