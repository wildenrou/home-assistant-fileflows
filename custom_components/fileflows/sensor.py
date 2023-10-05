from . import sensors_nodes
from . import sensors_server
from . import sensors_runners

async def async_setup_entry(hass, entry, async_add_devices):
    await sensors_server.async_setup_entry(hass, entry, async_add_devices)
    await sensors_nodes.async_setup_entry(hass, entry, async_add_devices)
    await sensors_runners.async_setup_entry(hass, entry, async_add_devices)
