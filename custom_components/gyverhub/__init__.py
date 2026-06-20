"""The GyverHub integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_PREFIX, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
from .coordinator import GyverHubCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GyverHub from a config entry."""
    _LOGGER.info("Setting up GyverHub integration for prefix: %s", entry.data[CONF_PREFIX])
    
    # Check if MQTT is available
    if "mqtt" not in hass.config.components:
        _LOGGER.error("MQTT integration is not available")
        return False
    
    # Get update interval from config
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    
    # Create coordinator
    coordinator = GyverHubCoordinator(
        hass,
        prefix=entry.data[CONF_PREFIX],
        entry_id=entry.entry_id,
        update_interval=update_interval,
    )
    
    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Start the coordinator (subscribe to MQTT topics)
    await coordinator.async_start()
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading GyverHub integration for prefix: %s", entry.data[CONF_PREFIX])
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Stop the coordinator
        coordinator: GyverHubCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_stop()
    
    return unload_ok
