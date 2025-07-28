"""FileFlows binary sensor platform."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
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
    """Set up FileFlows binary sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    # Create binary sensors
    sensors = [
        FileFlowsStatusBinarySensor(coordinator, config_entry),
        FileFlowsProcessingBinarySensor(coordinator, config_entry),
        FileFlowsNodesActiveBinarySensor(coordinator, config_entry),
    ]
    
    async_add_entities(sensors, update_before_add=True)


class FileFlowsBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for FileFlows binary sensors."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
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


class FileFlowsStatusBinarySensor(FileFlowsBaseBinarySensor):
    """Binary sensor for FileFlows server status."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Status"
        self._attr_unique_id = f"{self._host}_{self._port}_status"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_icon = "mdi:server"

    @property
    def is_on(self) -> bool:
        """Return True if the server is online."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "status" in self.coordinator.data
            and "error" not in self.coordinator.data.get("status", {})
        )

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.last_update_success:
            return {"status": "offline", "error": "Connection failed"}
        
        if self.coordinator.data is None:
            return {"status": "offline", "error": "No data"}
        
        status_data = self.coordinator.data.get("status", {})
        if "error" in status_data:
            return {"status": "offline", "error": status_data["error"]}
        
        return {
            "status": "online",
            "last_updated": self.coordinator.last_update_success_time,
            "queue": status_data.get("queue"),
            "processing": status_data.get("processing"),
            "processed": status_data.get("processed"),
        }


class FileFlowsProcessingBinarySensor(FileFlowsBaseBinarySensor):
    """Binary sensor for FileFlows processing status."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Processing Active"
        self._attr_unique_id = f"{self._host}_{self._port}_processing_active"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_icon = "mdi:cog"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "status" in self.coordinator.data
            and "error" not in self.coordinator.data.get("status", {})
        )

    @property
    def is_on(self) -> bool:
        """Return True if FileFlows is currently processing files."""
        if not self.available:
            return False
        
        status_data = self.coordinator.data.get("status", {})
        processing = status_data.get("processing", 0)
        return processing > 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        status_data = self.coordinator.data.get("status", {})
        processing_files = status_data.get("processingFiles", [])
        
        attributes = {
            "processing_count": status_data.get("processing", 0),
            "queue_count": status_data.get("queue", 0),
            "last_updated": self.coordinator.last_update_success_time,
        }
        
        # Add current processing file info
        if processing_files:
            current_file = processing_files[0]
            attributes.update({
                "current_file": current_file.get("name", "Unknown"),
                "current_step": current_file.get("step", "Unknown"),
                "current_percent": current_file.get("stepPercent", 0),
                "current_library": current_file.get("library", "Unknown"),
            })
        
        return attributes


class FileFlowsNodesActiveBinarySensor(FileFlowsBaseBinarySensor):
    """Binary sensor for active processing nodes."""

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_name = f"FileFlows Nodes Active"
        self._attr_unique_id = f"{self._host}_{self._port}_nodes_active"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_icon = "mdi:server-network"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "nodes" in self.coordinator.data
            and "error" not in self.coordinator.data.get("nodes", {})
        )

    @property
    def is_on(self) -> bool:
        """Return True if there are active nodes."""
        if not self.available:
            return False
        
        nodes_data = self.coordinator.data.get("nodes", {})
        nodes = nodes_data.get("nodes", nodes_data.get("workers", []))
        
        if isinstance(nodes, list):
            active_nodes = [n for n in nodes if n.get("enabled", True)]
            return len(active_nodes) > 0
        
        return False

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.available:
            return {}
        
        nodes_data = self.coordinator.data.get("nodes", {})
        nodes = nodes_data.get("nodes", nodes_data.get("workers", []))
        
        if isinstance(nodes, list):
            active_nodes = [n for n in nodes if n.get("enabled", True)]
            return {
                "total_nodes": len(nodes),
                "active_nodes": len(active_nodes),
                "node_names": [n.get("name", "Unknown") for n in active_nodes],
                "last_updated": self.coordinator.last_update_success_time,
            }
        
        return {}
