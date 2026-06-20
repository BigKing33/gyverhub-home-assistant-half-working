"""Number platform for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_UI_UPDATED
from .coordinator import GyverHubCoordinator
from .protocol import GyverHubDevice, SliderWidget

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GyverHub number entities from a config entry."""
    coordinator: GyverHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    added_entities: set[str] = set()
    
    @callback
    def async_add_entities_for_device(device: GyverHubDevice) -> None:
        """Add number entities for a device."""
        new_entities = []
        
        for slider in device.sliders:
            unique_id = f"{device.unique_id}_{slider.id}"
            if unique_id not in added_entities:
                added_entities.add(unique_id)
                new_entities.append(
                    GyverHubSlider(coordinator=coordinator, device=device, widget=slider)
                )
        
        if new_entities:
            _LOGGER.info(
                "Adding %d number entities for device %s",
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


class GyverHubSlider(NumberEntity):
    """Representation of a GyverHub slider (number input)."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: GyverHubCoordinator,
        device: GyverHubDevice,
        widget: SliderWidget,
    ) -> None:
        """Initialize the slider."""
        self.coordinator = coordinator
        self._device = device
        self._widget = widget
        
        self._attr_unique_id = f"{device.unique_id}_{widget.id}"
        self._attr_name = widget.label or widget.id
        
        self._attr_native_min_value = widget.min_value
        self._attr_native_max_value = widget.max_value
        self._attr_native_step = widget.step
        
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
            for slider in device.sliders:
                if slider.id == self._widget.id:
                    self._widget = slider
                    self.async_write_ha_state()
                    break

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        try:
            return float(self._widget.value) if self._widget.value is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._widget.disabled

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self.coordinator.async_set_widget_value(self._device, self._widget.id, value)
        self._widget.value = value
        self.async_write_ha_state()
