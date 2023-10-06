
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME


class ServerEntity(CoordinatorEntity):

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self._config_entry = config_entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"{NAME} {self._config_entry.title} Server",
            "manufacturer": NAME,
            "model": f"{NAME} Server"
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }

    @property
    def _unique_id_prefix(self):
        return f"{self._config_entry.entry_id}_server"


class NodeEntity(CoordinatorEntity):

    def __init__(self, coordinator, config_entry, node_uid: str):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._node_uid = node_uid

    @property
    def _data(self):
        return [d for d in self.coordinator.data if d["Uid"] == self._node_uid][0]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id, self._node_uid)},
            "name": f"{NAME} {self._config_entry.title} {self._data['Name']} Node",
            "manufacturer": NAME,
            "model": f"{NAME} Node",
            "sw_version": self._data["Version"],
            "via_device": (DOMAIN, self._config_entry.entry_id), # Server Device ID
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }

    @property
    def _unique_id_prefix(self):
        clean_node_name = self._data["Name"].lower().replace(" ", "_")
        return f"{self._config_entry.entry_id}_{clean_node_name}"


class RunnerEntity(CoordinatorEntity):

    def __init__(self, coordinator, config_entry, node_info, runner_idx: str):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._node_id = node_info["id"]
        self._node_name = node_info.get("name")
        self._runner_idx = runner_idx

    @property
    def _data(self):
        active_node_runners = [d for d in self.coordinator.data if d.get("NodeUid") == self._node_id]

        if self._runner_idx < len(active_node_runners):
            return active_node_runners[self._runner_idx]
        return {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id, self._node_id, self._runner_idx)},
            "name": f"{NAME} {self._config_entry.title} {self._node_name} Runner {self._runner_idx + 1}",
            "manufacturer": NAME,
            "model": f"{NAME} Runner",
            "via_device": (DOMAIN, self._config_entry.entry_id, self._node_id), # Node Device ID
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }

    @property
    def _unique_id_prefix(self):
        return f"{self._config_entry.entry_id}_{self._node_id}_{self._runner_idx}"
