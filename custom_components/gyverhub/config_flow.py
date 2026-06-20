"""Config flow for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_PREFIX, DEFAULT_PREFIX, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PREFIX, default=DEFAULT_PREFIX): str,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=10.0)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # Check if MQTT is available
    if "mqtt" not in hass.config.components:
        raise CannotConnect("MQTT integration is not configured")
    
    prefix = data[CONF_PREFIX].strip()
    if not prefix:
        raise InvalidPrefix("Prefix cannot be empty")
    
    return {"title": f"GyverHub ({prefix})"}


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidPrefix(Exception):
    """Error to indicate invalid prefix."""


class GyverHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GyverHub."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidPrefix:
                errors["base"] = "invalid_prefix"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if this prefix is already configured
                prefix = user_input[CONF_PREFIX].strip()
                update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                await self.async_set_unique_id(f"gyverhub_{prefix}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_PREFIX: prefix,
                        CONF_UPDATE_INTERVAL: update_interval,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
