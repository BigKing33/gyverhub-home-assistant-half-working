"""
GyverHub Device Model
Represents a discovered GyverHub device and its widgets
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum


class DeviceStatus(Enum):
    """Device online status"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class ButtonWidget:
    """Represents a button widget from GyverHub UI"""
    id: str
    label: str = ""
    color: int = 0x2E8B57  # Default green
    icon: Optional[str] = None
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ButtonWidget':
        """Create ButtonWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            color=data.get("color", 0x2E8B57),
            icon=data.get("icon"),
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )
    
    def get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.color >> 16) & 0xFF
        g = (self.color >> 8) & 0xFF
        b = self.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"


@dataclass
class SwitchWidget:
    """Represents a switch widget (type 2)"""
    id: str
    label: str = ""
    value: bool = False
    color: int = 0x2E8B57
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SwitchWidget':
        """Create SwitchWidget from UI JSON dictionary"""
        value_raw = data.get("value", data.get("#30", 0))
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=bool(int(value_raw)) if isinstance(value_raw, str) else bool(value_raw),
            color=data.get("color", 0x2E8B57),
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )


@dataclass
class LedWidget:
    """Represents a LED widget (type 3) - on/off indicator"""
    id: str
    label: str = ""
    value: bool = False
    color: int = 0xFF0000
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LedWidget':
        """Create LedWidget from UI JSON dictionary"""
        value_raw = data.get("value", data.get("#30", 0))
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=bool(int(value_raw)) if isinstance(value_raw, str) else bool(value_raw),
            color=data.get("color", 0xFF0000),
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )


@dataclass
class LabelWidget:
    """Represents a label widget (type 4) - read-only text"""
    id: str
    label: str = ""
    value: str = ""
    color: int = 0xFFFFFF
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LabelWidget':
        """Create LabelWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=str(data.get("value", data.get("#30", ""))),
            color=data.get("color", 0xFFFFFF),
            hint=data.get("hint")
        )


@dataclass
class InputWidget:
    """Represents an input widget (type 5) - text input"""
    id: str
    label: str = ""
    value: str = ""
    color: int = 0x2E8B57
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InputWidget':
        """Create InputWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=str(data.get("value", data.get("#30", ""))),
            color=data.get("color", 0x2E8B57),
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )


@dataclass
class SliderWidget:
    """Represents a slider widget (type 6) - numeric input"""
    id: str
    label: str = ""
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 100.0
    step: float = 1.0
    color: int = 0x2E8B57
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SliderWidget':
        """Create SliderWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=float(data.get("value", data.get("#30", 0))),
            min_value=float(data.get("min", data.get("#35", 0))),
            max_value=float(data.get("max", data.get("#36", 100))),
            step=float(data.get("step", data.get("#37", 1))),
            color=data.get("color", 0x2E8B57),
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )


@dataclass
class GaugeWidget:
    """Represents a gauge widget (type 7) - read-only numeric display"""
    id: str
    label: str = ""
    value: float = 0.0
    min_value: float = 0.0
    max_value: float = 100.0
    color: int = 0x2E8B57
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GaugeWidget':
        """Create GaugeWidget from UI JSON dictionary"""
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=float(data.get("value", data.get("#30", 0))),
            min_value=float(data.get("min", data.get("#35", 0))),
            max_value=float(data.get("max", data.get("#36", 100))),
            color=data.get("color", 0x2E8B57),
            hint=data.get("hint")
        )


@dataclass
class SelectWidget:
    """Represents a select widget (type 15) - dropdown selection"""
    id: str
    label: str = ""
    value: int = 0
    options: List[str] = field(default_factory=list)
    color: int = 0x2E8B57
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SelectWidget':
        """Create SelectWidget from UI JSON dictionary"""
        # Options can be in 'text' or '#5d' field
        options_str = data.get("#5d", data.get("text", ""))
        options = options_str.split(";") if options_str else []
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=int(data.get("value", data.get("#30", 0))),
            options=options,
            color=data.get("color", 0x2E8B57),
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )


@dataclass
class ColorWidget:
    """Represents a color picker widget (type 16) - RGB color input"""
    id: str
    label: str = ""
    value: int = 0xFFFFFF  # RGB color
    disabled: bool = False
    hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ColorWidget':
        """Create ColorWidget from UI JSON dictionary"""
        value_raw = data.get("value", data.get("#30", 0xFFFFFF))
        return cls(
            id=data.get("id", data.get("name", "")),
            label=data.get("label", data.get("text", "")),
            value=int(value_raw) if value_raw else 0xFFFFFF,
            disabled=data.get("disable", False),
            hint=data.get("hint")
        )
    
    def get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.value >> 16) & 0xFF
        g = (self.value >> 8) & 0xFF
        b = self.value & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"


@dataclass
class Device:
    """Represents a GyverHub device"""
    device_id: str
    prefix: str
    name: str = ""
    icon: str = ""
    version: str = ""
    platform: str = ""
    status: DeviceStatus = DeviceStatus.UNKNOWN
    
    # UI widgets
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
    
    # Callbacks
    on_status_change: Optional[Callable[['Device'], None]] = None
    on_ui_update: Optional[Callable[['Device'], None]] = None
    
    @property
    def unique_id(self) -> str:
        """Unique identifier combining prefix and device_id"""
        return f"{self.prefix}_{self.device_id}"
    
    def update_status(self, status: DeviceStatus):
        """Update device status and trigger callback"""
        if self.status != status:
            self.status = status
            if self.on_status_change:
                self.on_status_change(self)
    
    def update_ui(self, controls: List[Dict]):
        """Update UI from controls list"""
        from .protocol import GyverHubProtocol
        
        self.raw_ui = controls
        
        # Extract all widget types
        widgets = GyverHubProtocol.extract_widgets_by_type(controls)
        
        self.buttons = [ButtonWidget.from_dict(w) for w in widgets.get("button", [])]
        self.switches = [SwitchWidget.from_dict(w) for w in widgets.get("switch", [])]
        self.leds = [LedWidget.from_dict(w) for w in widgets.get("led", [])]
        self.labels = [LabelWidget.from_dict(w) for w in widgets.get("label", [])]
        self.inputs = [InputWidget.from_dict(w) for w in widgets.get("input", [])]
        self.sliders = [SliderWidget.from_dict(w) for w in widgets.get("slider", [])]
        self.gauges = [GaugeWidget.from_dict(w) for w in widgets.get("gauge", [])]
        self.selects = [SelectWidget.from_dict(w) for w in widgets.get("select", [])]
        self.colors = [ColorWidget.from_dict(w) for w in widgets.get("color", [])]
        
        if self.on_ui_update:
            self.on_ui_update(self)
    
    def get_button(self, button_id: str) -> Optional[ButtonWidget]:
        """Get a button by its ID"""
        for btn in self.buttons:
            if btn.id == button_id:
                return btn
        return None
    
    def get_widget_by_id(self, widget_id: str):
        """Get any widget by its ID"""
        for widget_list in [self.buttons, self.switches, self.leds, self.labels, 
                           self.inputs, self.sliders, self.gauges, self.selects, self.colors]:
            for widget in widget_list:
                if widget.id == widget_id:
                    return widget
        return None


class DeviceManager:
    """Manages multiple GyverHub devices across different prefixes"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}  # unique_id -> Device
        self.on_device_added: Optional[Callable[[Device], None]] = None
        self.on_device_removed: Optional[Callable[[Device], None]] = None
    
    def add_device(self, device: Device) -> bool:
        """
        Add a device to the manager.
        
        Returns:
            True if new device added, False if already exists
        """
        if device.unique_id in self.devices:
            # Update existing device info
            existing = self.devices[device.unique_id]
            existing.name = device.name
            existing.version = device.version
            existing.platform = device.platform
            existing.icon = device.icon
            return False
        
        self.devices[device.unique_id] = device
        if self.on_device_added:
            self.on_device_added(device)
        return True
    
    def remove_device(self, unique_id: str) -> bool:
        """Remove a device from the manager"""
        if unique_id in self.devices:
            device = self.devices.pop(unique_id)
            if self.on_device_removed:
                self.on_device_removed(device)
            return True
        return False
    
    def get_device(self, prefix: str, device_id: str) -> Optional[Device]:
        """Get a device by prefix and device_id"""
        unique_id = f"{prefix}_{device_id}"
        return self.devices.get(unique_id)
    
    def get_device_by_unique_id(self, unique_id: str) -> Optional[Device]:
        """Get a device by its unique_id"""
        return self.devices.get(unique_id)
    
    def get_all_devices(self) -> List[Device]:
        """Get all managed devices"""
        return list(self.devices.values())
    
    def get_devices_by_prefix(self, prefix: str) -> List[Device]:
        """Get all devices with a specific prefix"""
        return [d for d in self.devices.values() if d.prefix == prefix]
    
    def clear(self):
        """Remove all devices"""
        self.devices.clear()
