
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

    def __init__(self, coordinator, config_entry, runner_uid: str):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._runner_uid = runner_uid

    @property
    def _data(self):
        return [d for d in self.coordinator.data if d["Uid"] == self._runner_uid][0]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id, self._runner_uid)},
            "name": f"{NAME} {self._config_entry.title} {self._data['NodeName']} Runner", # TODO: Add an identifier for multiple runners
            "manufacturer": NAME,
            "model": f"{NAME} Runner",
            "via_device": (DOMAIN, self._config_entry.entry_id, self._data["NodeUid"]), # Node Device ID
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "integration": DOMAIN,
        }

    @property
    def _unique_id_prefix(self):
        return f"{self._config_entry.entry_id}_{self._runner_uid}"
