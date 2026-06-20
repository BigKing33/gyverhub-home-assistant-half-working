"""Light platform for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_RGB_COLOR,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_UI_UPDATED
from .coordinator import GyverHubCoordinator
from .protocol import GyverHubDevice, ColorWidget, GyverHubProtocol

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GyverHub light entities from a config entry."""
    coordinator: GyverHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    added_entities: set[str] = set()
    
    @callback
    def async_add_entities_for_device(device: GyverHubDevice) -> None:
        """Add light entities for a device."""
        new_entities = []
        
        # Add Color widgets as RGB lights
        for color in device.colors:
            unique_id = f"{device.unique_id}_{color.id}"
            if unique_id not in added_entities:
                added_entities.add(unique_id)
                new_entities.append(
                    GyverHubColorLight(coordinator=coordinator, device=device, widget=color)
                )
        
        if new_entities:
            _LOGGER.info(
                "Adding %d light entities for device %s",
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


class GyverHubColorLight(LightEntity):
    """Representation of a GyverHub color picker (RGB light).
    
    Note: Home Assistant will display a toggle/switch for this entity because
    it's a LightEntity. The toggle doesn't do anything useful for a pure color
    picker, but it's part of Home Assistant's standard UI for lights.
    
    For a better UI experience without the toggle, consider using:
    - custom:button-card with color_type: card and tap_action to open more-info
    - custom:mushroom-light-card with show_brightness_control: false
    - card-mod to hide the toggle: |
      ha-card { --toggle-display: none; }
    
    Alternatively, this could be reimplemented as a different entity type,
    but Home Assistant doesn't have a native color-picker-only entity.
    """

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: GyverHubCoordinator,
        device: GyverHubDevice,
        widget: ColorWidget,
    ) -> None:
        """Initialize the color light."""
        self.coordinator = coordinator
        self._device = device
        self._widget = widget
        
        self._attr_unique_id = f"{device.unique_id}_{widget.id}"
        self._attr_name = widget.label or widget.id
        
        # Disable this light from being the primary entity control
        self._attr_entity_registry_visible_default = True
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.unique_id)},
            name=device.name,
            manufacturer="GyverHub",
            model=device.platform or "Unknown",
            sw_version=device.version,
        )
        
        if widget.icon:
            self._attr_icon = f"mdi:{widget.icon}"

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
            for color in device.colors:
                if color.id == self._widget.id:
                    self._widget = color
                    self.async_write_ha_state()
                    break

    @property
    def is_on(self) -> bool:
        """Return true if the light is on (color picker is always considered 'on')."""
        # For a pure color picker, we consider it always on
        # This removes the toggle but Home Assistant may still show one in UI
        return True

    @property  
    def supported_features(self) -> int:
        """Flag supported features - no features for pure color picker."""
        return 0

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        """Return the RGB color."""
        return self._widget.rgb_color

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._widget.disabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set the color (no on/off, just color change)."""
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            color_int = GyverHubProtocol.color_to_int(r, g, b)
            await self.coordinator.async_set_widget_value(self._device, self._widget.id, color_int)
            self._widget.rgb_color = (r, g, b)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Not supported - color picker doesn't turn off."""
        pass
