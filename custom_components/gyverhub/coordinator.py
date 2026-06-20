"""Data coordinator for GyverHub integration."""
from __future__ import annotations

import logging
from typing import Dict, Optional, Callable, Any
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.components import mqtt
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    DEFAULT_CLIENT_ID,
    SIGNAL_DEVICE_DISCOVERED,
    SIGNAL_DEVICE_UI_UPDATED,
)
from .protocol import (
    GyverHubProtocol,
    ParsedMessage,
    MessageType,
    GyverHubDevice,
    DeviceStatus,
)

_LOGGER = logging.getLogger(__name__)


class GyverHubCoordinator:
    """Coordinator for GyverHub device discovery and communication."""

    def __init__(self, hass: HomeAssistant, prefix: str, entry_id: str, update_interval: float = 3.0) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.prefix = prefix
        self.entry_id = entry_id
        self.client_id = f"{DEFAULT_CLIENT_ID}_{entry_id[:8]}"
        self.update_interval = update_interval
        
        # Discovered devices: device_id -> GyverHubDevice
        self.devices: Dict[str, GyverHubDevice] = {}
        
        # MQTT subscription unsubscribe callbacks
        self._unsubscribes: list[Callable[[], None]] = []
        
        # Auto-refresh timer cancel callback
        self._refresh_cancel: Optional[Callable[[], None]] = None
        
        # Flag to track if we're running
        self._running = False

    async def async_start(self) -> None:
        """Start the coordinator and subscribe to MQTT topics."""
        if self._running:
            return
            
        _LOGGER.info("Starting GyverHub coordinator for prefix: %s", self.prefix)
        
        # Subscribe to discovery topic (prefix)
        unsub1 = await mqtt.async_subscribe(
            self.hass,
            self.prefix,
            self._handle_mqtt_message,
            qos=0,
        )
        self._unsubscribes.append(unsub1)
        
        # Subscribe to hub responses (prefix/hub/#)
        unsub2 = await mqtt.async_subscribe(
            self.hass,
            f"{self.prefix}/hub/#",
            self._handle_mqtt_message,
            qos=0,
        )
        self._unsubscribes.append(unsub2)
        
        self._running = True
        
        # Send initial discovery request
        await self.async_discover_devices()
        
        # Setup auto-refresh timer (using configured interval)
        self._refresh_cancel = async_track_time_interval(
            self.hass,
            self._async_refresh_all_devices,
            timedelta(seconds=self.update_interval),
        )

    async def async_stop(self) -> None:
        """Stop the coordinator and unsubscribe from MQTT topics."""
        _LOGGER.info("Stopping GyverHub coordinator for prefix: %s", self.prefix)
        
        # Cancel auto-refresh timer
        if self._refresh_cancel:
            self._refresh_cancel()
            self._refresh_cancel = None
        
        for unsub in self._unsubscribes:
            unsub()
        self._unsubscribes.clear()
        
        self._running = False

    async def async_discover_devices(self) -> None:
        """Send discovery request to find devices."""
        _LOGGER.debug("Sending discovery request to prefix: %s", self.prefix)
        await mqtt.async_publish(
            self.hass,
            self.prefix,
            self.client_id,
            qos=0,
            retain=False,
        )
    
    async def _async_refresh_all_devices(self, now=None) -> None:
        """Refresh UI for all devices (called by timer)."""
        for device in self.devices.values():
            await self.async_request_ui(device)

    async def async_request_ui(self, device: GyverHubDevice) -> None:
        """Request UI definition from a device."""
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.client_id,
            "ui"
        )
        _LOGGER.debug("Requesting UI from device %s: %s", device.device_id, topic)
        await mqtt.async_publish(
            self.hass,
            topic,
            "",
            qos=0,
            retain=False,
        )

    async def async_click_button(self, device: GyverHubDevice, button_id: str) -> None:
        """Send a button click to a device."""
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.client_id,
            "set",
            button_id
        )
        payload = GyverHubProtocol.build_button_click_payload()
        
        _LOGGER.debug("Clicking button %s on device %s", button_id, device.device_id)
        await mqtt.async_publish(
            self.hass,
            topic,
            payload,
            qos=0,
            retain=False,
        )

    async def async_set_widget_value(self, device: GyverHubDevice, widget_id: str, value: any) -> None:
        """Set a widget value on a device."""
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.client_id,
            "set",
            widget_id
        )
        payload = GyverHubProtocol.build_set_payload(value)
        
        _LOGGER.debug("Setting widget %s on device %s to %s", widget_id, device.device_id, value)
        await mqtt.async_publish(
            self.hass,
            topic,
            payload,
            qos=0,
            retain=False,
        )
        
        # Update local state
        device.update_widget_value(widget_id, value)
        
        # Request UI refresh after 100ms to get updated values
        async def _delayed_refresh():
            await self.hass.async_add_executor_job(lambda: None)  # Small delay
            await self.async_request_ui(device)
        
        self.hass.async_create_task(_delayed_refresh())

    async def async_ping_device(self, device: GyverHubDevice) -> None:
        """Ping a device to check if it's alive."""
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.client_id,
            "ping"
        )
        await mqtt.async_publish(
            self.hass,
            topic,
            "",
            qos=0,
            retain=False,
        )

    def get_device(self, device_id: str) -> Optional[GyverHubDevice]:
        """Get a device by its device_id."""
        return self.devices.get(device_id)

    def get_all_devices(self) -> list[GyverHubDevice]:
        """Get all discovered devices."""
        return list(self.devices.values())

    @callback
    def _handle_mqtt_message(self, msg: mqtt.ReceiveMessage) -> None:
        """Handle incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload
            
            # Decode payload if bytes
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8')
            
            # Log raw message for debugging
            _LOGGER.debug("MQTT raw: topic=%s, payload_len=%d", topic, len(payload))
            _LOGGER.debug("MQTT payload: %s", payload[:500] if len(payload) > 500 else payload)
            
            # Check for status messages
            if "/status" in topic:
                self._handle_status_message(topic, payload)
                return
            
            # Check for get messages (widget updates)
            if "/get/" in topic:
                self._handle_get_message(topic, payload)
                return
            
            # Parse GyverHub protocol message
            parsed = GyverHubProtocol.parse_message(payload)
            if not parsed:
                _LOGGER.warning("Failed to parse message from %s (not GyverHub format?)", topic)
                _LOGGER.debug("Unparseable payload: %s", payload[:200])
                return
            
            _LOGGER.info(
                "Parsed message: type=%s, device_id=%s, has_controls=%s",
                parsed.msg_type,
                parsed.device_id,
                bool(parsed.controls)
            )
            
            # Handle by message type
            if parsed.msg_type == MessageType.DISCOVER:
                self.hass.async_create_task(self._handle_discover(parsed))
            elif parsed.msg_type == MessageType.UI:
                self._handle_ui(parsed)
            elif parsed.msg_type == MessageType.ACK:
                self._handle_ack(parsed)
            elif parsed.msg_type == MessageType.UPDATE:
                self._handle_update(parsed)
            else:
                _LOGGER.debug("Unhandled message type: %s", parsed.msg_type)
                
        except Exception as e:
            _LOGGER.error("Error processing MQTT message: %s", e, exc_info=True)

    def _handle_status_message(self, topic: str, payload: str) -> None:
        """Handle device status (online/offline) messages."""
        parts = topic.split("/")
        if len(parts) >= 4:
            device_id = parts[2]
            
            device = self.devices.get(device_id)
            if device:
                status = DeviceStatus.ONLINE if payload == "online" else DeviceStatus.OFFLINE
                device.status = status
                _LOGGER.info("Device %s status: %s", device_id, status.value)

    def _handle_get_message(self, topic: str, payload: str) -> None:
        """Handle widget value updates."""
        _LOGGER.debug("Widget update: %s = %s", topic, payload)

    async def _handle_discover(self, msg: ParsedMessage) -> None:
        """Handle device discovery response."""
        _LOGGER.info(
            "Device discovered: id=%s, name=%s, prefix=%s",
            msg.device_id,
            msg.device_name,
            msg.prefix
        )
        
        # Use message prefix or fallback to our prefix
        prefix = msg.prefix or self.prefix
        
        device = GyverHubDevice(
            device_id=msg.device_id,
            prefix=prefix,
            name=msg.device_name or msg.device_id,
            icon=msg.icon or "",
            version=msg.version or "",
            platform=msg.platform or "",
            status=DeviceStatus.ONLINE
        )
        
        is_new = msg.device_id not in self.devices
        self.devices[msg.device_id] = device
        
        if is_new:
            _LOGGER.info("New device added: %s (%s)", device.name, device.device_id)
            
            # Request UI for new device
            await self.async_request_ui(device)
            
            # Signal that a new device was discovered
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_DEVICE_DISCOVERED}_{self.entry_id}",
                device
            )
        else:
            # Update existing device info
            existing = self.devices[msg.device_id]
            existing.name = device.name
            existing.version = device.version
            existing.platform = device.platform
            existing.icon = device.icon
            existing.status = DeviceStatus.ONLINE

    def _handle_ui(self, msg: ParsedMessage) -> None:
        """Handle UI definition response."""
        _LOGGER.info("UI message for device %s with %d controls", 
                      msg.device_id, 
                      len(msg.controls) if msg.controls else 0)
        
        if msg.controls:
            _LOGGER.debug("Raw controls structure: %s", msg.controls[:3] if len(msg.controls) > 3 else msg.controls)
        
        device = self.devices.get(msg.device_id)
        if device and msg.controls:
            device.update_ui(msg.controls)
            
            # Log all widget types found
            _LOGGER.info(
                "UI updated for %s: buttons=%d, switches=%d, sliders=%d, leds=%d, labels=%d, inputs=%d, gauges=%d, selects=%d, colors=%d",
                device.name,
                len(device.buttons),
                len(device.switches),
                len(device.sliders),
                len(device.leds),
                len(device.labels),
                len(device.inputs),
                len(device.gauges),
                len(device.selects),
                len(device.colors)
            )
            
            # Log individual widget IDs for debugging
            for slider in device.sliders:
                _LOGGER.debug("Found slider: id=%s, label=%s, min=%s, max=%s", 
                             slider.id, slider.label, slider.min_value, slider.max_value)
            for switch in device.switches:
                _LOGGER.debug("Found switch: id=%s, label=%s", switch.id, switch.label)
            for led in device.leds:
                _LOGGER.debug("Found LED: id=%s, label=%s", led.id, led.label)
            
            # Signal that UI was updated
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_DEVICE_UI_UPDATED}_{self.entry_id}",
                device
            )
            _LOGGER.debug("Dispatched UI update signal for device %s", device.device_id)
        elif not device:
            _LOGGER.warning("UI received for unknown device: %s (known devices: %s)", 
                           msg.device_id, list(self.devices.keys()))
        elif not msg.controls:
            _LOGGER.warning("UI message for device %s has no controls", msg.device_id)
            _LOGGER.info(
                "UI updated for %s: %d buttons found",
                device.name,
                len(device.buttons)
            )
            
            # Signal that UI was updated
            async_dispatcher_send(
                self.hass,
                f"{SIGNAL_DEVICE_UI_UPDATED}_{self.entry_id}",
                device
            )
        elif not device:
            _LOGGER.warning("UI received for unknown device: %s", msg.device_id)

    def _handle_ack(self, msg: ParsedMessage) -> None:
        """Handle button click acknowledgment."""
        _LOGGER.debug("ACK received for widget: %s on device %s", msg.name, msg.device_id)

    def _handle_update(self, msg: ParsedMessage) -> None:
        """Handle widget update message."""
        if msg.updates:
            _LOGGER.debug("Updates received for device %s: %s", msg.device_id, msg.updates)
