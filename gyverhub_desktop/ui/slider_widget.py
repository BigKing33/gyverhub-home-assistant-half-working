"""
GyverHub Slider Widget
Custom PyQt6 widget for rendering GyverHub slider (number input)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.device import SliderWidget


class GHSliderWidget(QWidget):
    """
    Custom widget representing a GyverHub slider.
    Allows numeric input via slider control.
    """
    
    # Signal emitted when slider value changes (widget_id, new_value)
    value_changed = pyqtSignal(str, float)
    
    def __init__(self, slider_widget: SliderWidget, parent=None):
        super().__init__(parent)
        self.slider_widget = slider_widget
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Top row: Label and value
        top_layout = QHBoxLayout()
        
        if self.slider_widget.label:
            title = QLabel(self.slider_widget.label)
            title.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            top_layout.addWidget(title)
        
        top_layout.addStretch()
        
        # Value display
        self.value_label = QLabel(str(self.slider_widget.value))
        self.value_label.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        top_layout.addWidget(self.value_label)
        
        layout.addLayout(top_layout)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(not self.slider_widget.disabled)
        
        # Calculate steps for integer conversion
        range_val = self.slider_widget.max_value - self.slider_widget.min_value
        steps = int(range_val / self.slider_widget.step)
        
        self.slider.setMinimum(0)
        self.slider.setMaximum(steps)
        
        # Set current value
        current_step = int((self.slider_widget.value - self.slider_widget.min_value) / self.slider_widget.step)
        self.slider.setValue(current_step)
        
        color = self._get_color_hex()
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid #555555;
                height: 8px;
                background: #333333;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                border: 2px solid {color};
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {color};
            }}
            QSlider::add-page:horizontal {{
                background: #333333;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 4px;
            }}
        """)
        
        if self.slider_widget.hint:
            self.slider.setToolTip(self.slider_widget.hint)
        
        self.slider.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.slider)
    
    def _get_color_hex(self) -> str:
        """Get color as hex string"""
        r = (self.slider_widget.color >> 16) & 0xFF
        g = (self.slider_widget.color >> 8) & 0xFF
        b = self.slider_widget.color & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _on_value_changed(self, step_value):
        """Handle slider value change"""
        # Convert step to actual value
        actual_value = self.slider_widget.min_value + (step_value * self.slider_widget.step)
        self.value_label.setText(str(actual_value))
        self.value_changed.emit(self.slider_widget.id, actual_value)
    
    def update_value(self, value: float):
        """Update the slider value programmatically"""
        self.slider.blockSignals(True)
        step_value = int((value - self.slider_widget.min_value) / self.slider_widget.step)
        self.slider.setValue(step_value)
        self.value_label.setText(str(value))
        self.slider.blockSignals(False)
