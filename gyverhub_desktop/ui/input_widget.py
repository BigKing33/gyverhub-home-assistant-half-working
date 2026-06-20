"""
GyverHub Input Widget
Custom PyQt6 widget for rendering GyverHub text input
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.device import InputWidget


class GHInputWidget(QWidget):
    """
    Custom widget representing a GyverHub text input.
    Allows user to enter text.
    """
    
    # Signal emitted when input is submitted (widget_id, new_value)
    value_changed = pyqtSignal(str, str)
    
    def __init__(self, input_widget: InputWidget, parent=None):
        super().__init__(parent)
        self.input_widget = input_widget
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Title label
        if self.input_widget.label:
            title = QLabel(self.input_widget.label)
            title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            layout.addWidget(title)
        
        # Line edit
        self.line_edit = QLineEdit(self.input_widget.value)
        self.line_edit.setEnabled(not self.input_widget.disabled)
        
        color = self._get_color_hex()
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: #333333;
                color: #FFFFFF;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 6px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {color};
            }}
            QLineEdit:disabled {{
                opacity: 0.5;
            }}
        """)
        
        if self.input_widget.hint:
            self.line_edit.setToolTip(self.input_widget.hint)
        
        # Emit signal on Return/Enter key
        self.line_edit.returnPressed.connect(self._on_return_pressed)
        
        layout.addWidget(self.line_edit)
    
    def _get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.input_widget.color >> 16) & 0xFF
        g = (self.input_widget.color >> 8) & 0xFF
        b = self.input_widget.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _on_return_pressed(self):
        """Handle Return key press"""
        new_value = self.line_edit.text()
        self.value_changed.emit(self.input_widget.id, new_value)
    
    def update_value(self, value: str):
        """Update the input value programmatically"""
        self.line_edit.blockSignals(True)
        self.line_edit.setText(value)
        self.line_edit.blockSignals(False)
