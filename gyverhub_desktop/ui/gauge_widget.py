"""
GyverHub Gauge Widget
Custom PyQt6 widget for rendering GyverHub gauge (read-only number display)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.device import GaugeWidget


class GHGaugeWidget(QWidget):
    """
    Custom widget representing a GyverHub gauge.
    Displays read-only numeric value with progress bar.
    """
    
    def __init__(self, gauge_widget: GaugeWidget, parent=None):
        super().__init__(parent)
        self.gauge_widget = gauge_widget
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Top row: Label and value
        top_layout = QHBoxLayout()
        
        if self.gauge_widget.label:
            title = QLabel(self.gauge_widget.label)
            title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        # Value display
        self.value_label = QLabel(str(self.gauge_widget.value))
        self.value_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        top_layout.addWidget(self.value_label)
        
        layout.addLayout(top_layout)
        
        # Progress bar as gauge
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(int(self.gauge_widget.min_value))
        self.progress_bar.setMaximum(int(self.gauge_widget.max_value))
        self.progress_bar.setValue(int(self.gauge_widget.value))
        
        color = self._get_color_hex()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #555555;
                border-radius: 5px;
                background-color: #333333;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        
        if self.gauge_widget.hint:
            self.progress_bar.setToolTip(self.gauge_widget.hint)
        
        layout.addWidget(self.progress_bar)
    
    def _get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.gauge_widget.color >> 16) & 0xFF
        g = (self.gauge_widget.color >> 8) & 0xFF
        b = self.gauge_widget.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def update_value(self, value: float):
        """Update the gauge value"""
        self.value_label.setText(str(value))
        self.progress_bar.setValue(int(value))
