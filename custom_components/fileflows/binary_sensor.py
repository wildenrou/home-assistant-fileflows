
import datetime
from dateutil import parser
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from .coordinator import NodeInfoDataUpdateCoordinator
from .const import CONF_CONNECTED_LAST_SEEN_TIMESPAN, DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN, DOMAIN
from .entity import NodeEntity

async def async_setup_entry(hass, entry, async_add_devices):
    # TODO: Work out how to add new nodes as they appear
    node_info_coordinator = hass.data[DOMAIN][entry.entry_id][NodeInfoDataUpdateCoordinator]
    for node in node_info_coordinator.data:
        async_add_devices([
            ConnectedNodeBinarySensor(node_info_coordinator, entry, node["Uid"])
        ])


class ConnectedNodeBinarySensor(NodeEntity, BinarySensorEntity):

    _attr_has_entity_name = True
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def unique_id(self):
        return f"{self._unique_id_prefix}_connected"

    @property
    def __raw_value(self) -> datetime:
        return parser.parse(self._data.get("LastSeen"))

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "last_seen": self.__raw_value
        }

    @property
    def is_on(self) -> bool | None:
        time_since_last_seen = datetime.datetime.now(datetime.timezone.utc) - self.__raw_value
        last_seen_timespan_disconnected = datetime.timedelta(minutes=self._config_entry.data.get(CONF_CONNECTED_LAST_SEEN_TIMESPAN, DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN))
        return bool(time_since_last_seen <= last_seen_timespan_disconnected)

    @property
    def icon(self) -> str | None:
        return "mdi:check-network-outline" if self.is_on else "mdi:close-network-outline"
