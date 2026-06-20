"""Switch platform for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_DEVICE_UI_UPDATED, SIGNAL_DEVICE_DISCOVERED
from .coordinator import GyverHubCoordinator
from .protocol import GyverHubDevice, SwitchWidget

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GyverHub switch entities from a config entry."""
    coordinator: GyverHubCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    added_entities: set[str] = set()
    
    @callback
    def async_add_entities_for_device(device: GyverHubDevice) -> None:
        """Add switch entities for a device."""
        new_entities = []
        
        for switch in device.switches:
            unique_id = f"{device.unique_id}_{switch.id}"
            
            if unique_id not in added_entities:
                added_entities.add(unique_id)
                new_entities.append(
                    GyverHubSwitch(
                        coordinator=coordinator,
                        device=device,
                        widget=switch,
                    )
                )
        
        if new_entities:
            _LOGGER.info(
                "Adding %d switch entities for device %s",
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


class GyverHubSwitch(SwitchEntity):
    """Representation of a GyverHub switch."""

    _attr_has_entity_name = True
    # Prevent this entity from being shown as the primary entity of the device
    # This avoids showing the switch twice (once as primary, once as individual entity)
    _attr_entity_category = None

    def __init__(
        self,
        coordinator: GyverHubCoordinator,
        device: GyverHubDevice,
        widget: SwitchWidget,
    ) -> None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._device = device
        self._widget = widget
        
        self._attr_unique_id = f"{device.unique_id}_{widget.id}"
        self._attr_name = widget.label or widget.id
        
        # Disable this switch from being the primary entity control
        # This prevents the switch from appearing twice (once as primary, once as widget)
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
            for switch in device.switches:
                if switch.id == self._widget.id:
                    self._widget = switch
                    self.async_write_ha_state()
                    break

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._widget.state

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._widget.disabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.async_set_widget_value(self._device, self._widget.id, 1)
        self._widget.state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.async_set_widget_value(self._device, self._widget.id, 0)
        self._widget.state = False
        self.async_write_ha_state()
