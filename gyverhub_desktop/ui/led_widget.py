"""
GyverHub LED Widget
Custom PyQt6 widget for rendering GyverHub LED indicators
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.device import LedWidget


class GHLedWidget(QWidget):
    """
    Custom widget representing a GyverHub LED indicator.
    Shows on/off state with colored circle.
    """
    
    def __init__(self, led: LedWidget, parent=None):
        super().__init__(parent)
        self.led = led
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Label
        if self.led.label:
            label = QLabel(self.led.label)
            label.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            layout.addWidget(label)
        
        layout.addStretch()
        
        # LED indicator
        self.indicator = QLabel("●")
        self.indicator.setFont(QFont("Segoe UI", 18))
        self.indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_indicator_color()
        
        if self.led.hint:
            self.indicator.setToolTip(self.led.hint)
        
        layout.addWidget(self.indicator)
    
    def _update_indicator_color(self):
        """Update indicator color based on LED state"""
        if self.led.value:
            color = self._get_color_hex()
        else:
            color = "#333333"  # Dark gray when off
        
        self.indicator.setStyleSheet(f"color: {color};")
    
    def _get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.led.color >> 16) & 0xFF
        g = (self.led.color >> 8) & 0xFF
        b = self.led.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def update_value(self, value: bool):
        """Update the LED state"""
        self.led.value = value
        self._update_indicator_color()
