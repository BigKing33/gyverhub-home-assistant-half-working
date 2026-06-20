"""
GyverHub Select Widget
Custom PyQt6 widget for rendering GyverHub select (dropdown)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.device import SelectWidget


class GHSelectWidget(QWidget):
    """
    Custom widget representing a GyverHub select (dropdown).
    Allows selection from predefined options.
    """
    
    # Signal emitted when selection changes (widget_id, new_index)
    value_changed = pyqtSignal(str, int)
    
    def __init__(self, select_widget: SelectWidget, parent=None):
        super().__init__(parent)
        self.select_widget = select_widget
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Title label
        if self.select_widget.label:
            title = QLabel(self.select_widget.label)
            title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            layout.addWidget(title)
        
        # Combo box
        self.combo_box = QComboBox()
        self.combo_box.setEnabled(not self.select_widget.disabled)
        
        # Add options
        for option in self.select_widget.options:
            self.combo_box.addItem(option)
        
        # Set current selection
        if 0 <= self.select_widget.value < len(self.select_widget.options):
            self.combo_box.setCurrentIndex(self.select_widget.value)
        
        color = self._get_color_hex()
        self.combo_box.setStyleSheet(f"""
            QComboBox {{
                background-color: #333333;
                color: #FFFFFF;
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 6px;
                font-size: 13px;
            }}
            QComboBox:focus {{
                border: 2px solid {color};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #FFFFFF;
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #333333;
                color: #FFFFFF;
                selection-background-color: {color};
                border: 2px solid #555555;
            }}
            QComboBox:disabled {{
                opacity: 0.5;
            }}
        """)
        
        if self.select_widget.hint:
            self.combo_box.setToolTip(self.select_widget.hint)
        
        self.combo_box.currentIndexChanged.connect(self._on_index_changed)
        
        layout.addWidget(self.combo_box)
    
    def _get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.select_widget.color >> 16) & 0xFF
        g = (self.select_widget.color >> 8) & 0xFF
        b = self.select_widget.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _on_index_changed(self, index):
        """Handle selection change"""
        self.value_changed.emit(self.select_widget.id, index)
    
    def update_value(self, index: int):
        """Update the selection programmatically"""
        self.combo_box.blockSignals(True)
        self.combo_box.setCurrentIndex(index)
        self.combo_box.blockSignals(False)
