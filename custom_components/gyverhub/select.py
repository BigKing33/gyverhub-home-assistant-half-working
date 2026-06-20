"""Select platform for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_UI_UPDATED
from .coordinator import GyverHubCoordinator
from .protocol import GyverHubDevice, SelectWidget

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GyverHub select entities from a config entry."""
    coordinator: GyverHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    added_entities: set[str] = set()
    
    @callback
    def async_add_entities_for_device(device: GyverHubDevice) -> None:
        """Add select entities for a device."""
        new_entities = []
        
        for select in device.selects:
            unique_id = f"{device.unique_id}_{select.id}"
            if unique_id not in added_entities:
                added_entities.add(unique_id)
                new_entities.append(
                    GyverHubSelect(coordinator=coordinator, device=device, widget=select)
                )
        
        if new_entities:
            _LOGGER.info(
                "Adding %d select entities for device %s",
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


class GyverHubSelect(SelectEntity):
    """Representation of a GyverHub select (dropdown)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GyverHubCoordinator,
        device: GyverHubDevice,
        widget: SelectWidget,
    ) -> None:
        """Initialize the select."""
        self.coordinator = coordinator
        self._device = device
        self._widget = widget
        
        self._attr_unique_id = f"{device.unique_id}_{widget.id}"
        self._attr_name = widget.label or widget.id
        self._attr_options = widget.options if widget.options else ["Option 0"]
        
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
            for select in device.selects:
                if select.id == self._widget.id:
                    self._widget = select
                    self._attr_options = select.options if select.options else ["Option 0"]
                    self.async_write_ha_state()
                    break

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        idx = self._widget.selected_index
        if 0 <= idx < len(self._attr_options):
            return self._attr_options[idx]
        return self._attr_options[0] if self._attr_options else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._widget.disabled

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in self._attr_options:
            idx = self._attr_options.index(option)
            await self.coordinator.async_set_widget_value(self._device, self._widget.id, idx)
            self._widget.selected_index = idx
            self._widget.value = idx
            self.async_write_ha_state()
