"""
GyverHub Protocol Parser
Handles parsing of GyverHub MQTT messages wrapped in #{...}#
"""
import json
import re
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


class MessageType(Enum):
    """Types of GyverHub messages"""
    DISCOVER = "discover"
    UI = "ui"
    ACK = "ack"
    OK = "OK"
    UPDATE = "update"
    ERROR = "error"
    INFO = "info"
    UNKNOWN = "unknown"


@dataclass
class ParsedMessage:
    """Parsed GyverHub message"""
    device_id: str
    client_id: str
    msg_type: MessageType
    raw_data: Dict[str, Any]
    
    # Optional fields depending on message type
    name: Optional[str] = None  # Widget name for ack
    controls: Optional[List[Dict]] = None  # UI controls
    updates: Optional[Dict] = None  # Update values
    error_code: Optional[int] = None  # Error code
    
    # Device info (from discover)
    device_name: Optional[str] = None
    prefix: Optional[str] = None
    icon: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None


class GyverHubProtocol:
    """Parser for GyverHub MQTT protocol"""
    
    # Pattern to extract JSON from #{...}# wrapper
    MESSAGE_PATTERN = re.compile(r'#\{(.+)\}#', re.DOTALL)
    
    # GyverHub short key mappings (from tags.h)
    SHORT_KEYS = {
        '#0': 'api_v',
        '#1': 'id',
        '#2': 'seq',
        '#3': 'client',
        '#4': 'updates',
        '#5': 'code',
        '#6': 'text',
        '#7': 'value',
        '#8': 'controls',
        '#9': 'type',
        '#a': 'name',
        '#b': 'prefix',
        '#c': 'icon',
        '#d': 'PIN',
        '#e': 'version',
        '#f': 'max_upl',
        '#10': 'http_t',
        '#11': 'ota_t',
        '#12': 'ws_port',
        '#13': 'modules',
        '#14': 'label',
        '#15': 'color',
        '#16': 'fsize',
        '#17': 'data',
        '#18': 'hint',
        '#19': 'disable',
        '#1a': 'wwidth',
        '#1b': 'notab',
        '#1c': 'nolabel',
        '#60': 'text',  # Button text/label
        '#68': 'wtype',  # Widget type (alternative encoding)
        '#69': 'color',  # Widget color
        '#79': 'platform',
    }
    
    # Widget short keys (context-dependent - used in controls array)
    WIDGET_SHORT_KEYS = {
        '#1': 'id',
        '#3': 'type',  # In widgets, #3 is the widget type
        '#60': 'text',
        '#68': 'type',  # Alternative widget type field
        '#69': 'color',
        '#14': 'label',
        '#15': 'color',
        '#7': 'value',
        '#18': 'hint',
        '#19': 'disable',
        '#17': 'data',
    }
    
    # Message type numeric codes
    TYPE_CODES = {
        0: 'unknown',
        1: 'set',
        2: 'read',
        3: 'get',
        4: 'status',
        5: 'ping',
        6: 'info',
        7: 'files',
        8: 'data',
        9: 'discover',
        10: 'ui',
        11: 'unfocus',
        12: 'cli',
        13: 'OK',
        14: 'ack',
        15: 'update',
        16: 'error',
        17: 'reboot',
        18: 'delete',
        19: 'rename',
        20: 'create',
        21: 'upload_chunk',
        22: 'upload_end',
        23: 'fetch_chunk',
        24: 'fetch_end',
        25: 'ota_url',
        26: 'ota_chunk',
        27: 'ota_end',
    }
    
    # Widget type codes
    WIDGET_TYPES = {
        0: 'row',
        1: 'button',
        2: 'switch',
        3: 'led',
        4: 'label',
        5: 'input',
        6: 'slider',
        7: 'gauge',
        8: 'spinner',
        9: 'joystick',
        10: 'dpad',
        11: 'tabs',
        12: 'canvas',
        13: 'display',
        14: 'datetime',
        15: 'select',
        16: 'color',
        17: 'flags',
        18: 'title',
        19: 'stream',
        # Extended hex codes (based on observed values from ESP devices)
        104: 'button',  # 0x68 - button variant
        102: 'switch',  # 0x66 - switch
        89: 'led',      # 0x59 - led
        96: 'label',    # 0x60 - label
        116: 'input',   # 0x74 - input
        108: 'slider',  # 0x6C - slider
        86: 'gauge',    # 0x56 - gauge
        106: 'select',  # 0x6A - select
        105: 'color',   # 0x69 - color
    }
    
    @classmethod
    def _expand_short_keys(cls, data: Dict[str, Any], is_widget: bool = False) -> Dict[str, Any]:
        """
        Recursively expand short keys to full keys in JSON data.
        Also converts numeric type/widget codes to strings.
        
        Args:
            data: Dictionary with potentially short keys
            is_widget: True if processing a widget inside controls array
            
        Returns:
            Dictionary with expanded keys
        """
        if not isinstance(data, dict):
            return data
        
        expanded = {}
        for key, value in data.items():
            # Expand key using appropriate mapping
            # For widgets, use WIDGET_SHORT_KEYS first, otherwise use SHORT_KEYS
            if is_widget and key in cls.WIDGET_SHORT_KEYS:
                expanded_key = cls.WIDGET_SHORT_KEYS[key]
            else:
                expanded_key = cls.SHORT_KEYS.get(key, key)
            
            # Determine if child items should be treated as widgets
            # Items in 'controls', 'data', or 'wwidth' arrays are widgets
            # (wwidth is used before expansion when #1a contains controls)
            is_child_widget = expanded_key in ['controls', 'data', 'wwidth']
            
            # Recursively expand nested structures
            if isinstance(value, dict):
                expanded_value = cls._expand_short_keys(value, is_child_widget)
            elif isinstance(value, list):
                expanded_value = [cls._expand_short_keys(item, is_child_widget) if isinstance(item, dict) else item 
                                  for item in value]
            else:
                expanded_value = value
            
            # Convert string codes like "#9" to integers first
            if isinstance(expanded_value, str) and expanded_value.startswith('#'):
                try:
                    # Remove # and convert hex to int
                    code_str = expanded_value[1:]
                    expanded_value = int(code_str, 16)
                except ValueError:
                    pass  # Keep as string if not valid hex
            
            # Convert type codes to strings (for message-level type field)
            if expanded_key == 'type' and isinstance(expanded_value, int) and not is_widget:
                expanded_value = cls.TYPE_CODES.get(expanded_value, str(expanded_value))
            
            # Convert widget type codes (for widget-level type field)
            if expanded_key == 'type' and isinstance(expanded_value, int) and is_widget:
                expanded_value = cls.WIDGET_TYPES.get(expanded_value, str(expanded_value))
            
            # Convert client codes to strings
            if expanded_key == 'client' and isinstance(expanded_value, int):
                expanded_value = cls.TYPE_CODES.get(expanded_value, str(expanded_value))
            
            # Legacy: Convert widget type codes for old #9 field
            if key == '#9' and isinstance(expanded_value, int):
                expanded_value = cls.WIDGET_TYPES.get(expanded_value, str(expanded_value))
            
            expanded[expanded_key] = expanded_value
        
        return expanded
    
    @classmethod
    def _fix_json_keys(cls, json_str: str) -> str:
        """
        Fix GyverHub JSON format by adding quotes around unquoted keys and special values.
        GyverHub sends JSON like {#1:"value",#3:#9,#a:123} which needs fixing:
        - Keys starting with # need quotes: #1 -> "#1"
        - Values that are # codes also need quotes: #9 -> "#9"
        
        Args:
            json_str: Raw JSON string with potentially unquoted keys
            
        Returns:
            Fixed JSON string with all keys and # values quoted
        """
        # Step 1: Quote all keys (pattern: { or , followed by #code followed by :)
        # Matches: {#1: or ,#a: or ,#79:
        json_str = re.sub(r'([{,\s])(#[0-9a-fA-F]+)(\s*:)', r'\1"\2"\3', json_str)
        
        # Step 2: Quote # values that are not already quoted
        # Matches: :#9 or :#a but not :"#9"
        json_str = re.sub(r':(\s*)(#[0-9a-fA-F]+)([,}\s])', r':"\2"\3', json_str)
        
        return json_str
    
    @classmethod
    def parse_message(cls, payload: str) -> Optional[ParsedMessage]:
        """
        Parse a GyverHub message from MQTT payload.
        Messages are wrapped in #{...}# delimiters.
        Handles both short key format (#1, #a) and long key format (id, name).
        
        Args:
            payload: Raw MQTT payload string
            
        Returns:
            ParsedMessage object or None if parsing fails
        """
        # Extract JSON from wrapper
        match = cls.MESSAGE_PATTERN.search(payload)
        if not match:
            return None
            
        try:
            json_str = "{" + match.group(1) + "}"
            
            # Fix unquoted keys in GyverHub JSON format
            json_str = cls._fix_json_keys(json_str)
            
            # Debug: log the fixed JSON
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Fixed JSON: {json_str[:200]}")
            
            data = json.loads(json_str)
            
            # Expand short keys to full keys
            data = cls._expand_short_keys(data)
            
        except json.JSONDecodeError as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"JSON parse error: {e} for payload: {payload[:200]}")
            return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Parse error: {e} for payload: {payload[:200]}")
            return None
        
        # Get message type - could be string or integer
        type_val = data.get("type", "unknown")
        if isinstance(type_val, int):
            type_str = cls.TYPE_CODES.get(type_val, "unknown")
        else:
            type_str = type_val
        
        # Get client_id - could be string or integer (type code)
        client_val = data.get("client", "")
        if isinstance(client_val, int):
            client_id = cls.TYPE_CODES.get(client_val, str(client_val))
        else:
            client_id = client_val
        
        # Special case: if client is a message type (like "discover"), it IS the type
        # In GyverHub, discovery messages don't have a separate type field
        if type_str == "unknown" and client_id in ["discover", "ui", "ack", "OK", "update", "error", "info"]:
            type_str = client_id
            # For discovery, client should be empty or the actual client that sent the discovery request
            client_id = ""
        
        # Special handling: wwidth field with array at root level = controls (UI message)
        # This happens when #1a contains the controls array in UI messages
        if "wwidth" in data and isinstance(data.get("wwidth"), list) and not data.get("controls"):
            data["controls"] = data.pop("wwidth")
            # If type is unknown and we have controls, it's a UI message
            if type_str == "unknown":
                type_str = "ui"
                
        try:
            msg_type = MessageType(type_str)
        except ValueError:
            msg_type = MessageType.UNKNOWN
        
        # Create base message
        msg = ParsedMessage(
            device_id=data.get("id", ""),
            client_id=client_id,
            msg_type=msg_type,
            raw_data=data
        )
        
        # Parse type-specific fields
        if msg_type == MessageType.DISCOVER:
            msg.device_name = data.get("name", "")
            msg.prefix = data.get("prefix", "")
            msg.icon = data.get("icon", "")
            msg.version = data.get("version", "")
            msg.platform = data.get("platform", "")
            
        elif msg_type == MessageType.UI:
            msg.controls = data.get("controls", [])
            logger.debug(f"UI message parsed: {len(msg.controls)} controls found")
            logger.debug(f"Controls data: {msg.controls}")
            msg.prefix = data.get("prefix", "")  # UI messages might have prefix too
            
        elif msg_type == MessageType.ACK:
            msg.name = data.get("name", "")
            
        elif msg_type == MessageType.UPDATE:
            msg.updates = data.get("updates", {})
            
        elif msg_type == MessageType.ERROR:
            msg.error_code = data.get("code", 0)
        
        return msg
    
    @classmethod
    def extract_buttons(cls, controls: List[Dict]) -> List[Dict]:
        """
        Extract button widgets from UI controls structure.
        Handles nested rows and containers.
        
        Args:
            controls: List of control dictionaries from UI message
            
        Returns:
            List of button widget dictionaries
        """
        buttons = []
        
        def _extract_recursive(items: List[Dict]):
            for item in items:
                widget_type = item.get("type", "")
                
                if widget_type == "button":
                    buttons.append(item)
                    
                # Check for nested controls in containers (row, tabs, etc.)
                if "data" in item and isinstance(item["data"], list):
                    _extract_recursive(item["data"])
                if "controls" in item and isinstance(item["controls"], list):
                    _extract_recursive(item["controls"])
        
        _extract_recursive(controls)
        return buttons
    
    @classmethod
    def extract_widgets_by_type(cls, controls: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract all widgets from UI controls structure grouped by type.
        Handles nested rows and containers.
        
        Args:
            controls: List of control dictionaries from UI message
            
        Returns:
            Dictionary mapping widget type to list of widget dictionaries
        """
        widgets = {
            "button": [],
            "switch": [],
            "led": [],
            "label": [],
            "input": [],
            "slider": [],
            "gauge": [],
            "select": [],
            "color": []
        }
        
        def _extract_recursive(items: List[Dict]):
            for item in items:
                widget_type = item.get("type", "")
                
                # Add to appropriate list if it's a supported widget type
                if widget_type in widgets:
                    widgets[widget_type].append(item)
                    
                # Check for nested controls in containers (row, tabs, etc.)
                if "data" in item and isinstance(item["data"], list):
                    _extract_recursive(item["data"])
                if "controls" in item and isinstance(item["controls"], list):
                    _extract_recursive(item["controls"])
        
        _extract_recursive(controls)
        return widgets
    
    @classmethod
    def build_topic(cls, prefix: str, device_id: str, client_id: str, 
                    command: str, widget_name: Optional[str] = None) -> str:
        """
        Build an MQTT topic for sending commands to a device.
        
        Args:
            prefix: Network prefix (e.g., "MyDevices")
            device_id: Device ID in hex format
            client_id: Client identifier
            command: Command type (ui, ping, set, read, etc.)
            widget_name: Optional widget name for set/read commands
            
        Returns:
            MQTT topic string
        """
        if widget_name:
            return f"{prefix}/{device_id}/{client_id}/{command}/{widget_name}"
        return f"{prefix}/{device_id}/{client_id}/{command}"
    
    @classmethod
    def build_button_click_payload(cls) -> str:
        """
        Get the payload for a button click.
        In GyverHub protocol, button click is value '2'.
        
        Returns:
            "2" as the click payload
        """
        return "2"
    
    @classmethod
    def int_to_color(cls, color_int: int) -> str:
        """
        Convert GyverHub integer color to hex string.
        
        Args:
            color_int: 24-bit color integer
            
        Returns:
            Hex color string like "#2E8B57"
        """
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
