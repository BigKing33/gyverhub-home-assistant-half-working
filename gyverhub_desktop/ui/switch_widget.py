"""
GyverHub Switch Widget
Custom PyQt6 widget for rendering GyverHub switch controls
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.device import SwitchWidget


class GHSwitchWidget(QWidget):
    """
    Custom widget representing a GyverHub switch.
    Styled to match GyverHub app appearance.
    """
    
    # Signal emitted when switch value changes (widget_id, new_value)
    value_changed = pyqtSignal(str, bool)
    
    def __init__(self, switch: SwitchWidget, parent=None):
        super().__init__(parent)
        self.switch = switch
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Label
        if self.switch.label:
            label = QLabel(self.switch.label)
            label.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            layout.addWidget(label)
        
        layout.addStretch()
        
        # Switch/Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.switch.value)
        self.checkbox.setEnabled(not self.switch.disabled)
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style the checkbox as a switch
        color = self._get_color_hex()
        self.checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background-color: #555555;
            }}
            QCheckBox::indicator:checked {{
                background-color: {color};
            }}
            QCheckBox::indicator:disabled {{
                opacity: 0.5;
            }}
        """)
        
        if self.switch.hint:
            self.checkbox.setToolTip(self.switch.hint)
        
        self.checkbox.stateChanged.connect(self._on_state_changed)
        layout.addWidget(self.checkbox)
    
    def _get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.switch.color >> 16) & 0xFF
        g = (self.switch.color >> 8) & 0xFF
        b = self.switch.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _on_state_changed(self, state):
        """Handle checkbox state change"""
        is_checked = state == Qt.CheckState.Checked.value
        self.value_changed.emit(self.switch.id, is_checked)
    
    def update_value(self, value: bool):
        """Update the switch value programmatically"""
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(value)
        self.checkbox.blockSignals(False)
