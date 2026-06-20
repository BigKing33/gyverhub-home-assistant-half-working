"""
GyverHub Color Widget
Custom PyQt6 widget for rendering GyverHub color picker
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QColorDialog, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

from core.device import ColorWidget


class GHColorWidget(QWidget):
    """
    Custom widget representing a GyverHub color picker.
    Allows RGB color selection.
    """
    
    # Signal emitted when color changes (widget_id, new_color_int)
    value_changed = pyqtSignal(str, int)
    
    def __init__(self, color_widget: ColorWidget, parent=None):
        super().__init__(parent)
        self.color_widget = color_widget
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Title label
        if self.color_widget.label:
            title = QLabel(self.color_widget.label)
            title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            layout.addWidget(title)
        
        # Color display button
        self.color_button = QPushButton()
        self.color_button.setEnabled(not self.color_widget.disabled)
        self.color_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_button.setMinimumHeight(40)
        
        self._update_button_color()
        
        if self.color_widget.hint:
            self.color_button.setToolTip(self.color_widget.hint)
        
        self.color_button.clicked.connect(self._on_button_clicked)
        
        layout.addWidget(self.color_button)
    
    def _update_button_color(self):
        """Update button to show current color"""
        hex_color = self.color_widget.get_color_hex()
        
        # Calculate text color based on brightness
        r = (self.color_widget.value >> 16) & 0xFF
        g = (self.color_widget.value >> 8) & 0xFF
        b = self.color_widget.value & 0xFF
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "#FFFFFF" if brightness < 128 else "#000000"
        
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                color: {text_color};
                border: 2px solid #555555;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #FFFFFF;
            }}
            QPushButton:disabled {{
                opacity: 0.5;
            }}
        """)
        
        self.color_button.setText(hex_color.upper())
    
    def _on_button_clicked(self):
        """Open color picker dialog"""
        current_color = QColor(self.color_widget.get_color_hex())
        
        color = QColorDialog.getColor(
            current_color, 
            self, 
            "Select Color",
            QColorDialog.ColorDialogOption.DontUseNativeDialog
        )
        
        if color.isValid():
            # Convert QColor to integer
            color_int = (color.red() << 16) | (color.green() << 8) | color.blue()
            self.color_widget.value = color_int
            self._update_button_color()
            self.value_changed.emit(self.color_widget.id, color_int)
    
    def update_value(self, color_int: int):
        """Update the color value programmatically"""
        self.color_widget.value = color_int
        self._update_button_color()
