"""Config flow for FileFlows integration - Conservative version."""
from __future__ import annotations

import logging
from typing import Any, Dict
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
    if CONF_URL in data and data[CONF_URL].strip():
        try:
            parsed = urlparse(data[CONF_URL].strip())
            host = parsed.hostname
            port = parsed.port or 8585
            if not host:
                raise InvalidHost("Invalid URL format - could not extract hostname")
        except Exception as err:
            raise InvalidHost(f"Invalid URL format: {err}") from err
    else:
        # Use direct host/port configuration
        host = data.get(CONF_HOST, "").strip()
        port = data.get(CONF_PORT, 8585)
        if not host:
            raise InvalidHost("Host is required when URL is not provided")
    
    # Clean up API key
    api_key = data.get(CONF_API_KEY, "").strip() or None
    
    _LOGGER.debug("Validating connection to %s:%s (API key: %s)", 
                  host, port, "provided" if api_key else "not provided")
    
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
            raise CannotConnect(f"Unable to connect to FileFlows server at {host}:{port}")
        
        # Get server info for validation
        status = await api_client.get_status()
        _LOGGER.debug("Got status data: %s", status)
        
        # Create title and unique ID
        name = data.get(CONF_NAME, f"FileFlows ({host})").strip()
        if not name:
            name = f"FileFlows ({host})"
            
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
        if "timeout" in str(err).lower() or "connection" in str(err).lower():
            raise CannotConnect(f"Cannot connect to FileFlows server: {err}") from err
        else:
            raise InvalidHost(f"Invalid response from FileFlows server: {err}") from err
    except Exception as err:
        _LOGGER.error("Unexpected error during validation: %s", err)
        raise CannotConnect(f"Unexpected error connecting to FileFlows: {err}") from err


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
                    default=user_input.get(CONF_NAME, "FileFlows Server")
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
                    max=300,
                    step=5, 
                    unit_of_measurement="s", 
                    mode=NumberSelectorMode.BOX
                )),
                
                vol.Required(
                    CONF_TIMEOUT, 
                    default=user_input.get(CONF_TIMEOUT, 10)
                ): NumberSelector(NumberSelectorConfig(
                    min=5, 
                    max=60, 
                    step=1, 
                    unit_of_measurement="s", 
                    mode=NumberSelectorMode.SLIDER
                )),
                
                vol.Required(
                    CONF_CONNECTED_LAST_SEEN_TIMESPAN, 
                    default=user_input.get(CONF_CONNECTED_LAST_SEEN_TIMESPAN, DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN)
                ): NumberSelector(NumberSelectorConfig(
                    min=1, 
                    max=30, 
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
                "api_key_note": "Leave blank - most FileFlows installations don't require authentication",
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate the host is invalid."""
