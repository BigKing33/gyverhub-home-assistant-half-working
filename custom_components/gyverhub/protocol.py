"""
GyverHub Protocol Parser for Home Assistant
Handles parsing of GyverHub MQTT messages wrapped in #{...}#
"""
import json
import re
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

_LOGGER = logging.getLogger(__name__)


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


class DeviceStatus(Enum):
    """Device online status"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class BaseWidget:
    """Base class for all GyverHub widgets"""
    id: str
    widget_type: str = ""
    label: str = ""
    color: int = 0x2E8B57  # Default green
    icon: Optional[str] = None
    disabled: bool = False
    hint: Optional[str] = None
    value: Any = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BaseWidget':
        """Create widget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type=data.get("type", ""),
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=data.get("value"),
        )
    
    def get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.color >> 16) & 0xFF
        g = (self.color >> 8) & 0xFF
        b = self.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"


@dataclass
class ButtonWidget(BaseWidget):
    """Represents a button widget from GyverHub UI"""
    pass


@dataclass
class SwitchWidget(BaseWidget):
    """Represents a switch widget from GyverHub UI"""
    state: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SwitchWidget':
        """Create SwitchWidget from UI JSON dictionary"""
        value_raw = data.get("value", data.get("#30", 0))
        value = int(value_raw) if isinstance(value_raw, str) else value_raw
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="switch",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=value,
            state=bool(value),
        )


@dataclass
class LedWidget(BaseWidget):
    """Represents a LED widget from GyverHub UI (on/off light)"""
    state: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LedWidget':
        """Create LedWidget from UI JSON dictionary"""
        value_raw = data.get("value", data.get("#30", 0))
        value = int(value_raw) if isinstance(value_raw, str) else value_raw
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="led",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=value,
            state=bool(value),
        )


@dataclass
class LabelWidget(BaseWidget):
    """Represents a label/text display widget from GyverHub UI"""
    text: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LabelWidget':
        """Create LabelWidget from UI JSON dictionary"""
        value = str(data.get("value", data.get("#30", data.get("text", ""))))
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="label",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=value,
            text=value,
        )


@dataclass
class InputWidget(BaseWidget):
    """Represents a text input widget from GyverHub UI"""
    text: str = ""
    max_length: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InputWidget':
        """Create InputWidget from UI JSON dictionary"""
        value = str(data.get("value", data.get("#30", "")))
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="input",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=value,
            text=value,
            max_length=int(data.get("max", data.get("#31", 0))),
        )


@dataclass
class SliderWidget(BaseWidget):
    """Represents a slider widget from GyverHub UI"""
    min_value: float = 0
    max_value: float = 100
    step: float = 1
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SliderWidget':
        """Create SliderWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="slider",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=float(data.get("value", data.get("#30", 0))),
            min_value=float(data.get("min", data.get("#35", 0))),
            max_value=float(data.get("max", data.get("#36", 100))),
            step=float(data.get("step", data.get("#37", 1))),
        )


@dataclass
class GaugeWidget(BaseWidget):
    """Represents a gauge widget from GyverHub UI (read-only numeric)"""
    min_value: float = 0
    max_value: float = 100
    unit: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GaugeWidget':
        """Create GaugeWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="gauge",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=float(data.get("value", data.get("#30", 0))),
            min_value=float(data.get("min", data.get("#35", 0))),
            max_value=float(data.get("max", data.get("#36", 100))),
            unit=str(data.get("unit", data.get("#39", ""))),
        )


@dataclass
class SelectWidget(BaseWidget):
    """Represents a select/dropdown widget from GyverHub UI"""
    options: List[str] = field(default_factory=list)
    selected_index: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SelectWidget':
        """Create SelectWidget from UI JSON dictionary"""
        # Options can be in #5d field or text field
        options_raw = data.get("#5d", data.get("text", data.get("options", "")))
        if isinstance(options_raw, str):
            options = [opt.strip() for opt in options_raw.split(";") if opt.strip()]
        else:
            options = list(options_raw) if options_raw else []
        
        value_raw = data.get("value", data.get("#30", 0))
        value = int(value_raw) if isinstance(value_raw, str) else value_raw
        
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="select",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=value,
            options=options,
            selected_index=value,
        )


@dataclass
class ColorWidget(BaseWidget):
    """Represents a color picker widget from GyverHub UI"""
    rgb_color: tuple = (255, 255, 255)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ColorWidget':
        """Create ColorWidget from UI JSON dictionary"""
        color_val_raw = data.get("value", data.get("#30", 0xFFFFFF))
        color_val = int(color_val_raw) if isinstance(color_val_raw, str) else color_val_raw
        
        if isinstance(color_val, int):
            r = (color_val >> 16) & 0xFF
            g = (color_val >> 8) & 0xFF
            b = color_val & 0xFF
        else:
            r, g, b = 255, 255, 255
        
        return cls(
            id=data.get("id", data.get("name", "")),
            widget_type="color",
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint"),
            value=color_val,
            rgb_color=(r, g, b),
        )


@dataclass
class GyverHubDevice:
    """Represents a GyverHub device"""
    device_id: str
    prefix: str
    name: str = ""
    icon: str = ""
    version: str = ""
    platform: str = ""
    status: DeviceStatus = DeviceStatus.UNKNOWN
    
    # UI widgets by type
    buttons: List[ButtonWidget] = field(default_factory=list)
    switches: List[SwitchWidget] = field(default_factory=list)
    leds: List[LedWidget] = field(default_factory=list)
    labels: List[LabelWidget] = field(default_factory=list)
    inputs: List[InputWidget] = field(default_factory=list)
    sliders: List[SliderWidget] = field(default_factory=list)
    gauges: List[GaugeWidget] = field(default_factory=list)
    selects: List[SelectWidget] = field(default_factory=list)
    colors: List[ColorWidget] = field(default_factory=list)
    
    # Raw UI data for future widget types
    raw_ui: List[Dict] = field(default_factory=list)
    
    @property
    def unique_id(self) -> str:
        """Unique identifier combining prefix and device_id"""
        return f"{self.prefix}_{self.device_id}"
    
    def update_ui(self, controls: List[Dict]):
        """Update UI from controls list"""
        self.raw_ui = controls
        
        # Extract all widget types
        all_widgets = GyverHubProtocol.extract_widgets(controls)
        
        self.buttons = [ButtonWidget.from_dict(w) for w in all_widgets if w.get("type") == "button"]
        self.switches = [SwitchWidget.from_dict(w) for w in all_widgets if w.get("type") == "switch"]
        self.leds = [LedWidget.from_dict(w) for w in all_widgets if w.get("type") == "led"]
        self.labels = [LabelWidget.from_dict(w) for w in all_widgets if w.get("type") == "label"]
        self.inputs = [InputWidget.from_dict(w) for w in all_widgets if w.get("type") == "input"]
        self.sliders = [SliderWidget.from_dict(w) for w in all_widgets if w.get("type") == "slider"]
        self.gauges = [GaugeWidget.from_dict(w) for w in all_widgets if w.get("type") == "gauge"]
        self.selects = [SelectWidget.from_dict(w) for w in all_widgets if w.get("type") == "select"]
        self.colors = [ColorWidget.from_dict(w) for w in all_widgets if w.get("type") == "color"]
    
    def get_button(self, button_id: str) -> Optional[ButtonWidget]:
        """Get a button by its ID"""
        for btn in self.buttons:
            if btn.id == button_id:
                return btn
        return None
    
    def get_widget_by_id(self, widget_id: str) -> Optional[BaseWidget]:
        """Get any widget by its ID"""
        all_widgets = (
            self.buttons + self.switches + self.leds + self.labels +
            self.inputs + self.sliders + self.gauges + self.selects + self.colors
        )
        for widget in all_widgets:
            if widget.id == widget_id:
                return widget
        return None
    
    def update_widget_value(self, widget_id: str, value: Any) -> bool:
        """Update a widget's value. Returns True if widget was found."""
        widget = self.get_widget_by_id(widget_id)
        if widget:
            widget.value = value
            # Update type-specific attributes
            if isinstance(widget, (SwitchWidget, LedWidget)):
                widget.state = bool(value)
            elif isinstance(widget, LabelWidget):
                widget.text = str(value)
            elif isinstance(widget, InputWidget):
                widget.text = str(value)
            elif isinstance(widget, SelectWidget):
                widget.selected_index = int(value) if isinstance(value, (int, float)) else 0
            elif isinstance(widget, ColorWidget) and isinstance(value, int):
                r = (value >> 16) & 0xFF
                g = (value >> 8) & 0xFF
                b = value & 0xFF
                widget.rgb_color = (r, g, b)
            return True
        return False


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
        '#60': 'text',
        '#68': 'wtype',
        '#69': 'color',
        '#79': 'platform',
    }
    
    # Widget short keys (context-dependent - used in controls array)
    WIDGET_SHORT_KEYS = {
        '#1': 'id',
        '#3': 'type',
        '#60': 'text',
        '#68': 'type',
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
        # Hex codes from ESP devices
        104: 'button',  # 0x68
        102: 'switch',  # 0x66
        89: 'led',      # 0x59
        96: 'label',    # 0x60
        116: 'input',   # 0x74
        108: 'slider',  # 0x6C
        86: 'gauge',    # 0x56
        106: 'select',  # 0x6A
        105: 'color',   # 0x69
    }
    
    @classmethod
    def _expand_short_keys(cls, data: Dict[str, Any], is_widget: bool = False, depth: int = 0) -> Dict[str, Any]:
        """Recursively expand short keys to full keys in JSON data.
        
        Args:
            data: Dictionary to expand
            is_widget: True if this dict represents a widget (inside controls/data array)
            depth: Recursion depth for debugging
        """
        if not isinstance(data, dict):
            return data
        
        expanded = {}
        for key, value in data.items():
            # Expand key using appropriate mapping
            # Use widget short keys if we're inside a controls/data array (is_widget=True)
            if is_widget and key in cls.WIDGET_SHORT_KEYS:
                expanded_key = cls.WIDGET_SHORT_KEYS[key]
            else:
                expanded_key = cls.SHORT_KEYS.get(key, key)
            
            # Determine if children should be treated as widgets
            # Items inside 'controls', 'data', or 'wwidth' arrays are widgets
            children_are_widgets = expanded_key in ['controls', 'data', 'wwidth']
            
            # Recursively expand nested structures
            if isinstance(value, dict):
                # A direct dict child inherits parent's widget context OR becomes widget if parent is container
                expanded_value = cls._expand_short_keys(value, is_widget or children_are_widgets, depth + 1)
            elif isinstance(value, list):
                # For lists: if this is controls/data/wwidth, each item is a widget
                if children_are_widgets:
                    expanded_value = [cls._expand_short_keys(item, True, depth + 1) if isinstance(item, dict) else item 
                                      for item in value]
                else:
                    expanded_value = [cls._expand_short_keys(item, is_widget, depth + 1) if isinstance(item, dict) else item 
                                      for item in value]
            else:
                expanded_value = value
            
            # Convert string codes like "#9" to integers first
            if isinstance(expanded_value, str) and expanded_value.startswith('#'):
                try:
                    code_str = expanded_value[1:]
                    expanded_value = int(code_str, 16)
                except ValueError:
                    pass
            
            # Convert type codes to strings based on context
            if expanded_key == 'type' and isinstance(expanded_value, int):
                if is_widget:
                    # Inside widget context: use widget type codes
                    expanded_value = cls.WIDGET_TYPES.get(expanded_value, str(expanded_value))
                else:
                    # Top-level message: use message type codes
                    expanded_value = cls.TYPE_CODES.get(expanded_value, str(expanded_value))
            
            # Also handle 'wtype' key which is an alias for widget type
            if expanded_key == 'wtype' and isinstance(expanded_value, int):
                expanded_value = cls.WIDGET_TYPES.get(expanded_value, str(expanded_value))
                # Normalize to 'type' for consistency
                expanded_key = 'type'
            
            if expanded_key == 'client' and isinstance(expanded_value, int):
                expanded_value = cls.TYPE_CODES.get(expanded_value, str(expanded_value))
            
            expanded[expanded_key] = expanded_value
        
        return expanded
    
    @classmethod
    def _fix_json_keys(cls, json_str: str) -> str:
        """Fix GyverHub JSON format by adding quotes around unquoted keys."""
        json_str = re.sub(r'([{,\s])(#[0-9a-fA-F]+)(\s*:)', r'\1"\2"\3', json_str)
        json_str = re.sub(r':(\s*)(#[0-9a-fA-F]+)([,}\s])', r':"\2"\3', json_str)
        return json_str
    
    @classmethod
    def parse_message(cls, payload: str) -> Optional[ParsedMessage]:
        """Parse a GyverHub message from MQTT payload."""
        match = cls.MESSAGE_PATTERN.search(payload)
        if not match:
            return None
            
        try:
            json_str = "{" + match.group(1) + "}"
            json_str = cls._fix_json_keys(json_str)
            
            _LOGGER.debug("Fixed JSON: %s", json_str[:200])
            
            data = json.loads(json_str)
            data = cls._expand_short_keys(data)
            
        except json.JSONDecodeError as e:
            _LOGGER.error("JSON parse error: %s for payload: %s", e, payload[:200])
            return None
        except Exception as e:
            _LOGGER.error("Parse error: %s for payload: %s", e, payload[:200])
            return None
        
        type_val = data.get("type", "unknown")
        if isinstance(type_val, int):
            type_str = cls.TYPE_CODES.get(type_val, "unknown")
        else:
            type_str = str(type_val) if type_val else "unknown"
        
        client_val = data.get("client", "")
        if isinstance(client_val, int):
            client_id = cls.TYPE_CODES.get(client_val, str(client_val))
        else:
            client_id = str(client_val) if client_val else ""
        
        # Fallback: use client as type if type is unknown
        if type_str == "unknown" and client_id in ["discover", "ui", "ack", "OK", "update", "error", "info"]:
            type_str = client_id
            client_id = ""
        
        # Handle wwidth as controls alias
        if "wwidth" in data and isinstance(data.get("wwidth"), list) and not data.get("controls"):
            data["controls"] = data.pop("wwidth")
            if type_str == "unknown":
                type_str = "ui"
        
        # CRITICAL FALLBACK: Detect UI message by structure if type is still unknown
        # If message has 'controls' array with items, it's a UI message
        if type_str == "unknown" and "controls" in data and isinstance(data.get("controls"), list):
            if len(data["controls"]) > 0:
                type_str = "ui"
                _LOGGER.info("Detected UI message by structure (controls array with %d items)", len(data["controls"]))
        
        _LOGGER.debug("Message type detection: type_val=%s -> type_str=%s, client=%s", type_val, type_str, client_id)
                
        try:
            msg_type = MessageType(type_str)
        except ValueError:
            _LOGGER.warning("Unknown message type: %s, raw data keys: %s", type_str, list(data.keys()))
            msg_type = MessageType.UNKNOWN
        
        msg = ParsedMessage(
            device_id=data.get("id", ""),
            client_id=client_id,
            msg_type=msg_type,
            raw_data=data
        )
        
        if msg_type == MessageType.DISCOVER:
            msg.device_name = data.get("name", "")
            msg.prefix = data.get("prefix", "")
            msg.icon = data.get("icon", "")
            msg.version = data.get("version", "")
            msg.platform = data.get("platform", "")
            
        elif msg_type == MessageType.UI:
            msg.controls = data.get("controls", [])
            _LOGGER.debug("UI message parsed: %d controls found", len(msg.controls))
            msg.prefix = data.get("prefix", "")
            
        elif msg_type == MessageType.ACK:
            msg.name = data.get("name", "")
            
        elif msg_type == MessageType.UPDATE:
            msg.updates = data.get("updates", {})
            
        elif msg_type == MessageType.ERROR:
            msg.error_code = data.get("code", 0)
        
        return msg
    
    @classmethod
    def extract_buttons(cls, controls: List[Dict]) -> List[Dict]:
        """Extract button widgets from UI controls structure."""
        return [w for w in cls.extract_widgets(controls) if w.get("type") == "button"]
    
    @classmethod
    def extract_widgets(cls, controls: List[Dict], widget_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Extract widgets from UI controls structure.
        
        Args:
            controls: List of control dictionaries from UI message
            widget_types: Optional list of widget types to filter. If None, returns all.
        
        Returns:
            List of widget dictionaries
        """
        widgets = []
        widget_counter = [0]  # Use list to allow mutation in nested function
        
        # Widget types that represent actual controllable/displayable entities
        ENTITY_WIDGET_TYPES = {
            "button", "switch", "led", "label", "input", 
            "slider", "gauge", "select", "color"
        }
        
        def _extract_recursive(items: List[Dict]):
            for item in items:
                widget_type = item.get("type", "")
                
                _LOGGER.debug("Processing widget: type=%s, id=%s, keys=%s", 
                             widget_type, item.get("id", item.get("name", "<none>")), list(item.keys()))
                
                # Check if this is a widget we want
                if widget_type in ENTITY_WIDGET_TYPES:
                    # CRITICAL: Generate an ID if missing
                    if not item.get("id") and not item.get("name"):
                        auto_id = f"{widget_type}_{widget_counter[0]}"
                        item["id"] = auto_id
                        _LOGGER.debug("Auto-generated widget ID: %s for type %s", auto_id, widget_type)
                    
                    widget_counter[0] += 1
                    
                    if widget_types is None or widget_type in widget_types:
                        widgets.append(item)
                        _LOGGER.debug("Extracted widget: type=%s, id=%s", widget_type, item.get("id", item.get("name")))
                
                # Check for nested controls in containers (row, tabs, etc.)
                if "data" in item and isinstance(item["data"], list):
                    _extract_recursive(item["data"])
                if "controls" in item and isinstance(item["controls"], list):
                    _extract_recursive(item["controls"])
        
        _extract_recursive(controls)
        _LOGGER.info("Extracted %d widgets from %d controls", len(widgets), len(controls))
        return widgets
    
    @classmethod
    def build_topic(cls, prefix: str, device_id: str, client_id: str, 
                    command: str, widget_name: Optional[str] = None) -> str:
        """Build an MQTT topic for sending commands to a device."""
        if widget_name:
            return f"{prefix}/{device_id}/{client_id}/{command}/{widget_name}"
        return f"{prefix}/{device_id}/{client_id}/{command}"
    
    @classmethod
    def build_button_click_payload(cls) -> str:
        """Get the payload for a button click."""
        return "2"
    
    @classmethod
    def build_set_payload(cls, value: Any) -> str:
        """Build payload for setting a widget value."""
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)
    
    @classmethod
    def int_to_color(cls, color_int: int) -> str:
        """Convert GyverHub integer color to hex string."""
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    @classmethod
    def color_to_int(cls, r: int, g: int, b: int) -> int:
        """Convert RGB values to GyverHub integer color."""
        return (r << 16) | (g << 8) | b
