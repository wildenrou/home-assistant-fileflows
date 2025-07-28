"""Config flow for FileFlows integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_URL, CONF_TIMEOUT, CONF_SCAN_INTERVAL, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    TextSelector, 
    TextSelectorConfig, 
    TextSelectorType, 
    NumberSelector, 
    NumberSelectorConfig, 
    NumberSelectorMode
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import FileFlowsApiClient, FileFlowsApiError
from .const import (
    DOMAIN, 
    CONF_API_KEY,
    CONF_CONNECTED_LAST_SEEN_TIMESPAN, 
    DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    # Extract host and port from URL if provided, or use direct host/port
    if CONF_URL in data and data[CONF_URL]:
        # Parse URL to extract host and port
        parsed = urlparse(data[CONF_URL])
        host = parsed.hostname
        port = parsed.port or 8585
        if not host:
            raise InvalidHost("Invalid URL format")
    else:
        # Use direct host/port configuration
        host = data.get(CONF_HOST)
        port = data.get(CONF_PORT, 8585)
        if not host:
            raise InvalidHost("Host is required")
    
    timeout = data.get(CONF_TIMEOUT, 10)
    api_key = data.get(CONF_API_KEY)
    
    # Create API client with session from Home Assistant
    session = async_create_clientsession(hass)
    api_client = FileFlowsApiClient(
        host=host,
        port=port,
        api_key=api_key,
        session=session,
    )
    
    try:
        # Test connection using the status endpoint
        if not await api_client.test_connection():
            raise CannotConnect("Unable to connect to FileFlows server")
        
        # Get server info for unique ID
        status = await api_client.get_status()
        
        # Create title and unique ID
        name = data.get(CONF_NAME, f"FileFlows ({host})")
        unique_id = f"{host}_{port}"
        
        return {
            "title": name,
            "unique_id": unique_id,
            "host": host,
            "port": port,
            "server_info": status,
        }
        
    except FileFlowsApiError as err:
        _LOGGER.error("API error during validation: %s", err)
        if "timeout" in str(err).lower():
            raise CannotConnect("Timeout connecting to FileFlows server") from err
        else:
            raise InvalidHost("Invalid host or API configuration") from err
    except Exception as err:
        _LOGGER.error("Unexpected error during validation: %s", err)
        raise CannotConnect("Unexpected error connecting to FileFlows") from err
    finally:
        # Don't close the session here since it's managed by Home Assistant
        pass


class FileFlowsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for FileFlows integration."""
    
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Validate the input
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                
                # Store the validated host/port back into user_input for consistency
                user_input[CONF_HOST] = info["host"]
                user_input[CONF_PORT] = info["port"]
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "invalid_host"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
        else:
            user_input = {}

        # Build the configuration schema
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, 
                    default=user_input.get(CONF_NAME, "")
                ): str,
                
                vol.Optional(
                    CONF_URL, 
                    default=user_input.get(CONF_URL, "")
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
                
                vol.Optional(
                    CONF_HOST,
                    default=user_input.get(CONF_HOST, "")
                ): str,
                
                vol.Optional(
                    CONF_PORT,
                    default=user_input.get(CONF_PORT, 8585)
                ): NumberSelector(NumberSelectorConfig(
                    min=1, 
                    max=65535, 
                    step=1, 
                    mode=NumberSelectorMode.BOX
                )),
                
                vol.Optional(
                    CONF_API_KEY,
                    default=user_input.get(CONF_API_KEY, "")
                ): str,
                
                vol.Required(
                    CONF_SCAN_INTERVAL, 
                    default=user_input.get(CONF_SCAN_INTERVAL, 30)
                ): NumberSelector(NumberSelectorConfig(
                    min=10, 
                    step=1, 
                    unit_of_measurement="s", 
                    mode=NumberSelectorMode.BOX
                )),
                
                vol.Required(
                    CONF_TIMEOUT, 
                    default=user_input.get(CONF_TIMEOUT, 10)
                ): NumberSelector(NumberSelectorConfig(
                    min=1, 
                    max=30, 
                    step=1, 
                    unit_of_measurement="s", 
                    mode=NumberSelectorMode.SLIDER
                )),
                
                vol.Required(
                    CONF_CONNECTED_LAST_SEEN_TIMESPAN, 
                    default=user_input.get(CONF_CONNECTED_LAST_SEEN_TIMESPAN, DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN)
                ): NumberSelector(NumberSelectorConfig(
                    min=1, 
                    max=10, 
                    step=1, 
                    unit_of_measurement="mins", 
                    mode=NumberSelectorMode.BOX
                ))
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "url_example": "http://192.168.1.18:8585",
                "host_example": "192.168.1.18",
                "port_example": "8585",
            },
        )

    async def __test_connection(self, url: str, timeout: int) -> bool:
        """Return true if connection is successful (legacy method for compatibility)."""
        try:
            # Parse URL to get host and port
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 8585
            
            if not host:
                return False
            
            # Create API client
            session = async_create_clientsession(self.hass)
            client = FileFlowsApiClient(host=host, port=port, session=session)
            
            # Test connection
            return await client.test_connection()
            
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Connection test failed")
            return False


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate the host is invalid."""
