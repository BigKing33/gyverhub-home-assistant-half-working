"""
GyverHub MQTT Client
Handles MQTT connection and communication with GyverHub devices
"""
import logging
from typing import Optional, Callable, Set, Dict, Any
from dataclasses import dataclass
import paho.mqtt.client as mqtt

from .protocol import GyverHubProtocol, ParsedMessage, MessageType
from .device import Device, DeviceManager, DeviceStatus

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    """MQTT connection configuration"""
    broker: str
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: str = "gyverhub_desktop"
    keepalive: int = 60


class GyverHubMQTT:
    """
    MQTT Client for GyverHub protocol.
    Handles discovery, UI fetching, and button interactions.
    """
    
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        
        # Prefixes we're monitoring
        self.prefixes: Set[str] = set()
        
        # Device manager
        self.device_manager = DeviceManager()
        
        # Callbacks
        self.on_connect: Optional[Callable[[bool], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None
        self.on_message: Optional[Callable[[ParsedMessage], None]] = None
        self.on_device_discovered: Optional[Callable[[Device], None]] = None
        self.on_button_ack: Optional[Callable[[str, str, str], None]] = None  # device_id, button_id, prefix
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection initiated successfully
        """
        try:
            # Create MQTT client (v2 API)
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.config.client_id
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set credentials if provided
            if self.config.username and self.config.password:
                self.client.username_pw_set(
                    self.config.username, 
                    self.config.password
                )
            
            # Connect
            logger.info(f"Connecting to {self.config.broker}:{self.config.port}")
            self.client.connect(
                self.config.broker,
                self.config.port,
                self.config.keepalive
            )
            
            # Start network loop in background thread
            self.client.loop_start()
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    def add_prefix(self, prefix: str):
        """
        Add a prefix to monitor for devices.
        Subscribes to relevant topics.
        
        Args:
            prefix: Network prefix (e.g., "MyDevices")
        """
        if prefix in self.prefixes:
            return
            
        self.prefixes.add(prefix)
        
        if self.connected and self.client:
            self._subscribe_prefix(prefix)
    
    def remove_prefix(self, prefix: str):
        """Remove a prefix and unsubscribe from its topics"""
        if prefix not in self.prefixes:
            return
            
        self.prefixes.discard(prefix)
        
        if self.connected and self.client:
            # Unsubscribe from prefix topics
            self.client.unsubscribe(prefix)
            self.client.unsubscribe(f"{prefix}/hub/#")
    
    def _subscribe_prefix(self, prefix: str):
        """Subscribe to topics for a prefix"""
        if not self.client:
            return
            
        # Subscribe to discovery topic
        self.client.subscribe(prefix)
        
        # Subscribe to all device responses
        # Format: prefix/hub/client_id/device_id or prefix/hub/device_id/...
        self.client.subscribe(f"{prefix}/hub/#")
        
        logger.info(f"Subscribed to prefix: {prefix}")
    
    def discover_devices(self, prefix: Optional[str] = None):
        """
        Send discovery request to find devices.
        
        Args:
            prefix: Specific prefix to discover, or None for all prefixes
        """
        if not self.connected or not self.client:
            return
            
        prefixes_to_discover = [prefix] if prefix else list(self.prefixes)
        
        for p in prefixes_to_discover:
            # Publish client_id to prefix topic to trigger discovery
            self.client.publish(p, self.config.client_id)
            logger.debug(f"Discovery request sent to: {p}")
    
    def request_ui(self, device: Device):
        """
        Request UI definition from a device.
        
        Args:
            device: Device to request UI from
        """
        if not self.connected or not self.client:
            return
            
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.config.client_id,
            "ui"
        )
        
        self.client.publish(topic, "")
        logger.debug(f"UI request sent to: {device.device_id}")
    
    def click_button(self, device: Device, button_id: str):
        """
        Send a button click to a device.
        
        Args:
            device: Target device
            button_id: ID of the button to click
        """
        if not self.connected or not self.client:
            return
            
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.config.client_id,
            "set",
            button_id
        )
        
        payload = GyverHubProtocol.build_button_click_payload()
        self.client.publish(topic, payload)
        logger.debug(f"Button click sent: {button_id} to {device.device_id}")
    
    def set_widget_value(self, device: Device, widget_id: str, value):
        """
        Send a widget value change to a device.
        
        Args:
            device: Target device
            widget_id: ID of the widget
            value: New value to set (can be int, float, str, bool)
        """
        if not self.connected or not self.client:
            return
            
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.config.client_id,
            "set",
            widget_id
        )
        
        # Convert value to string payload
        payload = str(value)
        self.client.publish(topic, payload)
        logger.debug(f"Widget value sent: {widget_id}={value} to {device.device_id}")
    
    def ping_device(self, device: Device):
        """Ping a device to check if it's alive"""
        if not self.connected or not self.client:
            return
            
        topic = GyverHubProtocol.build_topic(
            device.prefix,
            device.device_id,
            self.config.client_id,
            "ping"
        )
        
        self.client.publish(topic, "")
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """MQTT on_connect callback"""
        if reason_code == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            
            # Subscribe to all registered prefixes
            for prefix in self.prefixes:
                self._subscribe_prefix(prefix)
            
            if self.on_connect:
                self.on_connect(True)
        else:
            logger.error(f"Connection failed with code: {reason_code}")
            if self.on_connect:
                self.on_connect(False)
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """MQTT on_disconnect callback"""
        self.connected = False
        logger.info("Disconnected from MQTT broker")
        
        if self.on_disconnect:
            self.on_disconnect()
    
    def _on_message(self, client, userdata, msg: mqtt.MQTTMessage):
        """MQTT on_message callback"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Message received: {topic} -> {payload[:100]}...")
            
            # Check for status messages (online/offline)
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
                logger.debug(f"Failed to parse message from {topic}")
                return
            
            logger.debug(f"Parsed message: type={parsed.msg_type}, device_id={parsed.device_id}, client_id={parsed.client_id}")
            
            # Handle by message type
            if parsed.msg_type == MessageType.DISCOVER:
                self._handle_discover(parsed)
                
            elif parsed.msg_type == MessageType.UI:
                self._handle_ui(parsed)
                
            elif parsed.msg_type == MessageType.ACK:
                self._handle_ack(parsed)
                
            elif parsed.msg_type == MessageType.UPDATE:
                self._handle_update(parsed)
            
            # Call generic message callback
            if self.on_message:
                self.on_message(parsed)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _handle_status_message(self, topic: str, payload: str):
        """Handle device status (online/offline) messages"""
        # Topic format: prefix/hub/device_id/status
        parts = topic.split("/")
        if len(parts) >= 4:
            prefix = parts[0]
            device_id = parts[2]
            
            device = self.device_manager.get_device(prefix, device_id)
            if device:
                status = DeviceStatus.ONLINE if payload == "online" else DeviceStatus.OFFLINE
                device.update_status(status)
    
    def _handle_get_message(self, topic: str, payload: str):
        """Handle widget value updates"""
        # Topic format: prefix/hub/device_id/get/widget_name
        # For now, just log - can be extended for other widget types
        logger.debug(f"Widget update: {topic} = {payload}")
    
    def _handle_discover(self, msg: ParsedMessage):
        """Handle device discovery response"""
        logger.debug(f"Processing discover message: device_id={msg.device_id}, prefix={msg.prefix}, name={msg.device_name}")
        
        device = Device(
            device_id=msg.device_id,
            prefix=msg.prefix or "",
            name=msg.device_name or msg.device_id,
            icon=msg.icon or "",
            version=msg.version or "",
            platform=msg.platform or "",
            status=DeviceStatus.ONLINE
        )
        
        logger.debug(f"Created device object: unique_id={device.unique_id}")
        
        is_new = self.device_manager.add_device(device)
        
        logger.debug(f"Device added to manager: is_new={is_new}")
        
        if is_new:
            logger.info(f"Device discovered: {device.name} ({device.device_id})")
            
            if self.on_device_discovered:
                self.on_device_discovered(device)
            
            # Automatically request UI for new devices
            self.request_ui(device)
    
    def _handle_ui(self, msg: ParsedMessage):
        """Handle UI definition response"""
        logger.debug(f"Handling UI message: device_id={msg.device_id}, controls={msg.controls}")
        
        # Find prefix from response or try to match
        prefix = msg.prefix
        if not prefix:
            # Try to find device by ID across all prefixes
            for p in self.prefixes:
                device = self.device_manager.get_device(p, msg.device_id)
                if device:
                    prefix = p
                    break
        
        if not prefix:
            logger.warning(f"Cannot find prefix for device {msg.device_id}")
            return
            
        device = self.device_manager.get_device(prefix, msg.device_id)
        if device and msg.controls:
            logger.debug(f"Updating UI for device {device.name} with {len(msg.controls)} controls")
            device.update_ui(msg.controls)
            logger.info(f"UI updated for {device.name}: {len(device.buttons)} buttons")
        elif device and not msg.controls:
            logger.warning(f"UI message for {device.name} has no controls")
        elif not device:
            logger.warning(f"Device not found: {prefix}/{msg.device_id}")
    
    def _handle_ack(self, msg: ParsedMessage):
        """Handle button click acknowledgment"""
        logger.debug(f"ACK received for widget: {msg.name}")
        
        if self.on_button_ack and msg.name:
            # Find the device
            for device in self.device_manager.get_all_devices():
                if device.device_id == msg.device_id:
                    self.on_button_ack(msg.device_id, msg.name, device.prefix)
                    break
    
    def _handle_update(self, msg: ParsedMessage):
        """Handle widget update message"""
        if msg.updates:
            logger.debug(f"Updates received: {msg.updates}")
