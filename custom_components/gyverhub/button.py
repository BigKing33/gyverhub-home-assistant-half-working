"""Button platform for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_UI_UPDATED, SIGNAL_DEVICE_DISCOVERED
from .coordinator import GyverHubCoordinator
from .protocol import GyverHubDevice, ButtonWidget

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GyverHub button entities from a config entry."""
    coordinator: GyverHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Track which buttons we've already added
    added_buttons: set[str] = set()
    
    @callback
    def async_add_buttons_for_device(device: GyverHubDevice) -> None:
        """Add button entities for a device."""
        new_entities = []
        
        for button in device.buttons:
            unique_id = f"{device.unique_id}_{button.id}"
            
            if unique_id not in added_buttons:
                added_buttons.add(unique_id)
                new_entities.append(
                    GyverHubButton(
                        coordinator=coordinator,
                        device=device,
                        button=button,
                    )
                )
        
        if new_entities:
            _LOGGER.info(
                "Adding %d button entities for device %s",
                len(new_entities),
                device.name
            )
            async_add_entities(new_entities)
    
    # Listen for device discovery
    @callback
    def async_device_discovered(device: GyverHubDevice) -> None:
        """Handle newly discovered device."""
        _LOGGER.debug("Device discovered signal received: %s", device.device_id)
        # UI will be requested automatically, buttons will be added when UI is received
    
    # Listen for UI updates
    @callback
    def async_ui_updated(device: GyverHubDevice) -> None:
        """Handle device UI update."""
        _LOGGER.debug("UI updated signal received for device: %s", device.device_id)
        async_add_buttons_for_device(device)
    
    # Connect to dispatcher signals
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{SIGNAL_DEVICE_DISCOVERED}_{entry.entry_id}",
            async_device_discovered,
        )
    )
    
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{SIGNAL_DEVICE_UI_UPDATED}_{entry.entry_id}",
            async_ui_updated,
        )
    )
    
    # Add buttons for any devices that were already discovered
    for device in coordinator.get_all_devices():
        async_add_buttons_for_device(device)


class GyverHubButton(ButtonEntity):
    """Representation of a GyverHub button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GyverHubCoordinator,
        device: GyverHubDevice,
        button: ButtonWidget,
    ) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._device = device
        self._button = button
        
        # Entity attributes
        self._attr_unique_id = f"{device.unique_id}_{button.id}"
        self._attr_name = button.label or button.id
        
        # Device info for grouping entities
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.unique_id)},
            name=device.name,
            manufacturer="GyverHub",
            model=device.platform or "Unknown",
            sw_version=device.version,
        )
        
        # Set icon if available
        if button.icon:
            self._attr_icon = f"mdi:{button.icon}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._button.disabled

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info(
            "Button pressed: %s on device %s",
            self._button.id,
            self._device.name
        )
        await self.coordinator.async_click_button(self._device, self._button.id)
