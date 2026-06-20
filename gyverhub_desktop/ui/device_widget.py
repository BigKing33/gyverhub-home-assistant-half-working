"""
GyverHub Device Widget
Displays a device and its widgets
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont

from core.device import (
    Device, DeviceStatus, ButtonWidget, SwitchWidget, LedWidget,
    LabelWidget, InputWidget, SliderWidget, GaugeWidget, SelectWidget, ColorWidget
)
from .button_widget import GHButtonWidget
from .switch_widget import GHSwitchWidget
from .led_widget import GHLedWidget
from .label_widget import GHLabelWidget
from .input_widget import GHInputWidget
from .slider_widget import GHSliderWidget
from .gauge_widget import GHGaugeWidget
from .select_widget import GHSelectWidget
from .color_widget import GHColorWidget


class DeviceWidget(QFrame):
    """
    Widget displaying a GyverHub device with all its widgets.
    Shows device info header and grid of all control widgets.
    """
    
    # Signal emitted when a widget is interacted with (device_id, widget_id, value)
    widget_changed = pyqtSignal(str, str, object)
    
    # Signal to request UI refresh from device
    refresh_requested = pyqtSignal(str)  # device_id
    
    # Internal signals for thread-safe UI updates
    _ui_update_signal = pyqtSignal(object)  # Device object
    _status_change_signal = pyqtSignal(object)  # Device object
    
    def __init__(self, device: Device, parent=None):
        super().__init__(parent)
        self.device = device
        self.all_widgets = {}  # widget_id -> widget object
        
        self._setup_ui()
        self._populate_widgets()
        
        # Connect internal signals to slots (thread-safe)
        self._ui_update_signal.connect(self._on_ui_update_slot)
        self._status_change_signal.connect(self._on_status_change_slot)
        
        # Connect device callbacks to emit signals
        device.on_ui_update = lambda dev: self._ui_update_signal.emit(dev)
        device.on_status_change = lambda dev: self._status_change_signal.emit(dev)
        
        # Setup auto-refresh timer (every 3 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._request_refresh)
        self.refresh_timer.start(3000)  # 3 seconds
    
    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            DeviceWidget {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with device info
        header = self._create_header()
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3D3D3D;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Widgets container
        self.widgets_container = QWidget()
        self.widgets_layout = QGridLayout(self.widgets_container)
        self.widgets_layout.setSpacing(8)
        layout.addWidget(self.widgets_container)
        
        # Stretch to push content up
        layout.addStretch()
    
    def _create_header(self) -> QWidget:
        """Create device info header"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Device name
        self.name_label = QLabel(self.device.name or self.device.device_id)
        self.name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Platform info
        platform_label = QLabel(f"{self.device.platform} v{self.device.version}")
        platform_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(platform_label)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(self._get_status_style())
        self.status_indicator.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.status_indicator)
        
        # Device ID
        id_label = QLabel(f"[{self.device.device_id}]")
        id_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(id_label)
        
        return header
    
    def _get_status_style(self) -> str:
        """Get status indicator color based on device status"""
        if self.device.status == DeviceStatus.ONLINE:
            return "color: #00FF00;"
        elif self.device.status == DeviceStatus.OFFLINE:
            return "color: #FF0000;"
        return "color: #FFAA00;"  # Unknown = orange
    
    def _populate_widgets(self):
        """Create all widget types from device"""
        # Clear existing
        for widget in self.all_widgets.values():
            widget.deleteLater()
        self.all_widgets.clear()
        
        # Clear layout
        while self.widgets_layout.count():
            item = self.widgets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Check if device has any widgets
        total_widgets = (len(self.device.buttons) + len(self.device.switches) + 
                        len(self.device.leds) + len(self.device.labels) + 
                        len(self.device.inputs) + len(self.device.sliders) + 
                        len(self.device.gauges) + len(self.device.selects) + 
                        len(self.device.colors))
        
        if total_widgets == 0:
            # Show "No widgets" message
            no_widget_label = QLabel("No widgets available")
            no_widget_label.setStyleSheet("color: #666666; font-style: italic;")
            no_widget_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.widgets_layout.addWidget(no_widget_label, 0, 0)
            return
        
        # Add widgets in grid (2 columns for better layout)
        columns = 2
        row = 0
        col = 0
        
        # Helper to add widget to grid
        def add_to_grid(widget, widget_id):
            nonlocal row, col
            self.widgets_layout.addWidget(widget, row, col)
            self.all_widgets[widget_id] = widget
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        # Add buttons
        for button in self.device.buttons:
            btn_widget = GHButtonWidget(button)
            btn_widget.clicked.connect(lambda bid, b=button: self._on_widget_changed(b.id, 2))
            add_to_grid(btn_widget, button.id)
        
        # Add switches
        for switch in self.device.switches:
            switch_widget = GHSwitchWidget(switch)
            switch_widget.value_changed.connect(lambda wid, val: self._on_widget_changed(wid, 1 if val else 0))
            add_to_grid(switch_widget, switch.id)
        
        # Add LEDs (read-only, no interaction)
        for led in self.device.leds:
            led_widget = GHLedWidget(led)
            add_to_grid(led_widget, led.id)
        
        # Add labels (read-only)
        for label in self.device.labels:
            label_widget = GHLabelWidget(label)
            add_to_grid(label_widget, label.id)
        
        # Add inputs
        for input_w in self.device.inputs:
            input_widget = GHInputWidget(input_w)
            input_widget.value_changed.connect(lambda wid, val: self._on_widget_changed(wid, val))
            add_to_grid(input_widget, input_w.id)
        
        # Add sliders
        for slider in self.device.sliders:
            slider_widget = GHSliderWidget(slider)
            slider_widget.value_changed.connect(lambda wid, val: self._on_widget_changed(wid, val))
            add_to_grid(slider_widget, slider.id)
        
        # Add gauges (read-only)
        for gauge in self.device.gauges:
            gauge_widget = GHGaugeWidget(gauge)
            add_to_grid(gauge_widget, gauge.id)
        
        # Add selects
        for select in self.device.selects:
            select_widget = GHSelectWidget(select)
            select_widget.value_changed.connect(lambda wid, val: self._on_widget_changed(wid, val))
            add_to_grid(select_widget, select.id)
        
        # Add color pickers
        for color in self.device.colors:
            color_widget = GHColorWidget(color)
            color_widget.value_changed.connect(lambda wid, val: self._on_widget_changed(wid, val))
            add_to_grid(color_widget, color.id)
    
    def _on_widget_changed(self, widget_id: str, value):
        """Handle widget interaction"""
        self.widget_changed.emit(self.device.device_id, widget_id, value)
        # Request UI refresh after 100ms to get updated values
        QTimer.singleShot(100, lambda: self.refresh_requested.emit(self.device.device_id))
    
    def _request_refresh(self):
        """Request UI refresh from device"""
        self.refresh_requested.emit(self.device.device_id)
    
    @pyqtSlot(object)
    def _on_ui_update_slot(self, device: Device):
        """Called when device UI is updated (in Qt main thread)"""
        self.device = device
        self._update_widget_values()
    
    @pyqtSlot(object)
    def _on_status_change_slot(self, device: Device):
        """Called when device status changes (in Qt main thread)"""
        self.device = device
        self.status_indicator.setStyleSheet(self._get_status_style())
    
    def flash_widget(self, widget_id: str):
        """Flash a widget to show acknowledgment"""
        if widget_id in self.all_widgets:
            widget = self.all_widgets[widget_id]
            if hasattr(widget, 'flash_feedback'):
                widget.flash_feedback()
    
    def _update_widget_values(self):
        """Update existing widget values without recreating them"""
        # Update switches
        for switch in self.device.switches:
            if switch.id in self.all_widgets:
                widget = self.all_widgets[switch.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(switch.value)
        
        # Update LEDs
        for led in self.device.leds:
            if led.id in self.all_widgets:
                widget = self.all_widgets[led.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(led.value)
        
        # Update labels
        for label in self.device.labels:
            if label.id in self.all_widgets:
                widget = self.all_widgets[label.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(label.value)
        
        # Update inputs
        for input_w in self.device.inputs:
            if input_w.id in self.all_widgets:
                widget = self.all_widgets[input_w.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(input_w.value)
        
        # Update sliders
        for slider in self.device.sliders:
            if slider.id in self.all_widgets:
                widget = self.all_widgets[slider.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(slider.value)
        
        # Update gauges
        for gauge in self.device.gauges:
            if gauge.id in self.all_widgets:
                widget = self.all_widgets[gauge.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(gauge.value)
        
        # Update selects
        for select in self.device.selects:
            if select.id in self.all_widgets:
                widget = self.all_widgets[select.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(select.value)
        
        # Update colors
        for color in self.device.colors:
            if color.id in self.all_widgets:
                widget = self.all_widgets[color.id]
                if hasattr(widget, 'update_value'):
                    widget.update_value(color.value)
        
        # If structure changed (different widgets), recreate
        expected_count = (len(self.device.buttons) + len(self.device.switches) + 
                         len(self.device.leds) + len(self.device.labels) + 
                         len(self.device.inputs) + len(self.device.sliders) + 
                         len(self.device.gauges) + len(self.device.selects) + 
                         len(self.device.colors))
        if len(self.all_widgets) != expected_count:
            self._populate_widgets()
    
    def update_device(self, device: Device):
        """Update with new device data"""
        self.device = device
        self.name_label.setText(device.name or device.device_id)
        self.status_indicator.setStyleSheet(self._get_status_style())
        self._populate_widgets()
