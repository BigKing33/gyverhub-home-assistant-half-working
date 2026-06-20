"""Binary sensor platform for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_UI_UPDATED
from .coordinator import GyverHubCoordinator
from .protocol import GyverHubDevice, LedWidget

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GyverHub binary sensor entities from a config entry."""
    coordinator: GyverHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    added_entities: set[str] = set()
    
    @callback
    def async_add_entities_for_device(device: GyverHubDevice) -> None:
        """Add binary sensor entities for a device."""
        new_entities = []
        
        # Add LED widgets as binary sensors (status indicators)
        for led in device.leds:
            unique_id = f"{device.unique_id}_{led.id}"
            if unique_id not in added_entities:
                added_entities.add(unique_id)
                new_entities.append(
                    GyverHubLedIndicator(coordinator=coordinator, device=device, widget=led)
                )
        
        if new_entities:
            _LOGGER.info(
                "Adding %d binary sensor entities for device %s",
                len(new_entities),
                device.name
            )
            async_add_entities(new_entities)
    
    @callback
    def async_ui_updated(device: GyverHubDevice) -> None:
        """Handle device UI update."""
        async_add_entities_for_device(device)
    
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{SIGNAL_DEVICE_UI_UPDATED}_{entry.entry_id}",
            async_ui_updated,
        )
    )
    
    for device in coordinator.get_all_devices():
        async_add_entities_for_device(device)


class GyverHubLedIndicator(BinarySensorEntity):
    """Representation of a GyverHub LED (status indicator)."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.LIGHT

    def __init__(
        self,
        coordinator: GyverHubCoordinator,
        device: GyverHubDevice,
        widget: LedWidget,
    ) -> None:
        """Initialize the LED indicator."""
        self.coordinator = coordinator
        self._device = device
        self._widget = widget
        
        self._attr_unique_id = f"{device.unique_id}_{widget.id}"
        self._attr_name = widget.label or widget.id
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.unique_id)},
            name=device.name,
            manufacturer="GyverHub",
            model=device.platform or "Unknown",
            sw_version=device.version,
        )
        
        if widget.icon:
            self._attr_icon = f"mdi:{widget.icon}"
        else:
            self._attr_icon = "mdi:led-on" if widget.state else "mdi:led-off"

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_DEVICE_UI_UPDATED}_{self.coordinator.entry_id}",
                self._handle_ui_update,
            )
        )

    @callback
    def _handle_ui_update(self, device: GyverHubDevice) -> None:
        """Handle device UI update."""
        if device.device_id == self._device.device_id:
            # Find updated widget
            for led in device.leds:
                if led.id == self._widget.id:
                    self._widget = led
                    # Update icon based on new state
                    if not self._widget.icon:
                        self._attr_icon = "mdi:led-on" if self._widget.state else "mdi:led-off"
                    self.async_write_ha_state()
                    break

    @property
    def is_on(self) -> bool:
        """Return true if the LED is on."""
        return self._widget.state

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True
