from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_URL, CONF_TIMEOUT, CONF_SCAN_INTERVAL
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType, NumberSelector, NumberSelectorConfig, NumberSelectorMode
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import voluptuous as vol

from .api import FileFlowsApiClient
from .const import DOMAIN


class FileFlowsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for file flows integration"""
    # The schema version of the config
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, user_input):
        errors = {}

        if user_input is not None:
            # Test connection
            valid = await self.__test_connection(
                user_input[CONF_URL], user_input[CONF_TIMEOUT]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                errors["base"] = "connection_failed"
        else:
            user_input = {}

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=user_input.get(CONF_NAME) or ""): str,
                vol.Required(CONF_URL, default=user_input.get(CONF_URL) or ""): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
                vol.Required(CONF_SCAN_INTERVAL, default=user_input.get(CONF_SCAN_INTERVAL) or 30): NumberSelector(NumberSelectorConfig(min=10, step=1, unit_of_measurement="s", mode=NumberSelectorMode.BOX)),
                vol.Required(CONF_TIMEOUT, default=user_input.get(CONF_TIMEOUT) or 10): NumberSelector(NumberSelectorConfig(min=1, max=30, step=1, unit_of_measurement="s", mode=NumberSelectorMode.SLIDER))
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def __test_connection(self, url, timeout):
        """Return true if connection is successful."""
        try:
            session = async_create_clientsession(self.hass)
            client = FileFlowsApiClient(url, timeout, session)
            if await client.async_get_system_version():
                return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False
