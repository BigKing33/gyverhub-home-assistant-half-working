"""
GyverHub Button Widget
Custom PyQt6 widget for rendering GyverHub buttons
"""
from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QWidget, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPalette

from core.device import ButtonWidget


class GHButtonWidget(QWidget):
    """
    Custom widget representing a GyverHub button.
    Styled to match GyverHub app appearance.
    """
    
    # Signal emitted when button is clicked
    clicked = pyqtSignal(str)  # Emits button_id
    
    def __init__(self, button: ButtonWidget, parent=None):
        super().__init__(parent)
        self.button = button
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create the actual button
        self.btn = QPushButton()
        self.btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn.setMinimumHeight(45)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set button text
        label = self.button.label or self.button.id
        if self.button.icon:
            # For now just show label, icons need FontAwesome
            self.btn.setText(label)
        else:
            self.btn.setText(label)
        
        # Apply styling
        self._apply_style()
        
        # Set disabled state
        self.btn.setEnabled(not self.button.disabled)
        
        # Set tooltip/hint
        if self.button.hint:
            self.btn.setToolTip(self.button.hint)
        
        # Connect click signal
        self.btn.clicked.connect(self._on_clicked)
        
        layout.addWidget(self.btn)
    
    def _apply_style(self):
        """Apply GyverHub-style button appearance"""
        color = self.button.get_color_hex()
        
        # Calculate darker color for hover/pressed
        r = (self.button.color >> 16) & 0xFF
        g = (self.button.color >> 8) & 0xFF
        b = self.button.color & 0xFF
        
        # Darker variant (80%)
        dark_r = int(r * 0.8)
        dark_g = int(g * 0.8)
        dark_b = int(b * 0.8)
        dark_color = f"#{dark_r:02X}{dark_g:02X}{dark_b:02X}"
        
        # Lighter variant (120%)
        light_r = min(255, int(r * 1.2))
        light_g = min(255, int(g * 1.2))
        light_b = min(255, int(b * 1.2))
        light_color = f"#{light_r:02X}{light_g:02X}{light_b:02X}"
        
        # Determine text color based on brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "#FFFFFF" if brightness < 128 else "#000000"
        
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {light_color};
            }}
            QPushButton:pressed {{
                background-color: {dark_color};
            }}
            QPushButton:disabled {{
                background-color: #666666;
                color: #999999;
            }}
        """)
    
    def _on_clicked(self):
        """Handle button click"""
        self.clicked.emit(self.button.id)
    
    def update_button(self, button: ButtonWidget):
        """Update button properties"""
        self.button = button
        
        label = self.button.label or self.button.id
        self.btn.setText(label)
        self._apply_style()
        self.btn.setEnabled(not self.button.disabled)
        
        if self.button.hint:
            self.btn.setToolTip(self.button.hint)
    
    def flash_feedback(self):
        """Visual feedback when button action is acknowledged"""
        # Briefly change appearance to show acknowledgment
        original_style = self.btn.styleSheet()
        self.btn.setStyleSheet(original_style + """
            QPushButton {
                border: 3px solid #00FF00;
            }
        """)
        
        # Reset after 200ms using QTimer
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self.btn.setStyleSheet(original_style))
