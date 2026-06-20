"""
GyverHub Label Widget
Custom PyQt6 widget for rendering GyverHub label (read-only text)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.device import LabelWidget


class GHLabelWidget(QWidget):
    """
    Custom widget representing a GyverHub label (sensor).
    Displays read-only text value.
    """
    
    def __init__(self, label_widget: LabelWidget, parent=None):
        super().__init__(parent)
        self.label_widget = label_widget
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Title label
        if self.label_widget.label:
            title = QLabel(self.label_widget.label)
            title.setStyleSheet("color: #888888; font-size: 11px;")
            layout.addWidget(title)
        
        # Value label
        self.value_label = QLabel(self.label_widget.value)
        self.value_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        self.value_label.setWordWrap(True)
        
        if self.label_widget.hint:
            self.value_label.setToolTip(self.label_widget.hint)
        
        layout.addWidget(self.value_label)
    
    def update_value(self, value: str):
        """Update the label text"""
        self.value_label.setText(value)
