"""
GyverHub Desktop Main Window
Main application window with connection settings and device display
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QFrame, QMessageBox, QSpinBox, QSplitter,
    QListWidget, QListWidgetItem, QStackedWidget,
    QGroupBox, QFormLayout, QTextEdit, QStatusBar
)
from PyQt6.QtCore import Qt, QSettings, pyqtSlot, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon

from core.mqtt_client import GyverHubMQTT, MQTTConfig
from core.device import Device, DeviceManager
from core.protocol import ParsedMessage
from .device_widget import DeviceWidget


class MQTTSignals(QObject):
    """Signals for MQTT callbacks to communicate with Qt thread"""
    connected = pyqtSignal(bool)
    disconnected = pyqtSignal()
    device_discovered = pyqtSignal(object)  # Device object
    button_ack = pyqtSignal(str, str, str)  # device_id, button_id, prefix
    message_received = pyqtSignal(object)  # ParsedMessage
    log_message = pyqtSignal(str)  # Log text


class MainWindow(QMainWindow):
    """Main application window for GyverHub Desktop"""
    
    def __init__(self):
        super().__init__()
        
        self.mqtt_client: GyverHubMQTT = None
        self.device_widgets: dict[str, DeviceWidget] = {}
        self.settings = QSettings("GyverHub", "Desktop")
        
        # Create signals object for thread-safe communication
        self.mqtt_signals = MQTTSignals()
        self.mqtt_signals.connected.connect(self._on_mqtt_connected)
        self.mqtt_signals.disconnected.connect(self._on_mqtt_disconnected)
        self.mqtt_signals.device_discovered.connect(self._on_device_discovered)
        self.mqtt_signals.button_ack.connect(self._on_button_ack)
        self.mqtt_signals.message_received.connect(self._on_mqtt_message)
        
        self._setup_ui()
        self._load_settings()
        self._setup_connections()
    
    def _setup_ui(self):
        self.setWindowTitle("GyverHub Desktop")
        self.setMinimumSize(900, 600)
        self.resize(1200, 700)
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLineEdit, QSpinBox, QTextEdit {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                padding: 8px;
                color: #FFFFFF;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #0078D4;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084D8;
            }
            QPushButton:pressed {
                background-color: #006CBC;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3D3D3D;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
            QListWidget::item:hover {
                background-color: #3D3D3D;
            }
            QScrollArea {
                border: none;
            }
            QStatusBar {
                background-color: #2D2D2D;
                color: #888888;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left panel - Settings
        left_panel = self._create_settings_panel()
        left_panel.setFixedWidth(300)
        main_layout.addWidget(left_panel)
        
        # Right panel - Devices
        right_panel = self._create_devices_panel()
        main_layout.addWidget(right_panel, 1)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Disconnected")
    
    def _create_settings_panel(self) -> QWidget:
        """Create the left settings panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # MQTT Connection settings
        mqtt_group = QGroupBox("MQTT Broker")
        mqtt_layout = QFormLayout(mqtt_group)
        
        self.broker_input = QLineEdit()
        self.broker_input.setPlaceholderText("test.mosquitto.org")
        mqtt_layout.addRow("Broker:", self.broker_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(1883)
        mqtt_layout.addRow("Port:", self.port_input)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("(optional)")
        mqtt_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("(optional)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        mqtt_layout.addRow("Password:", self.password_input)
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setText("gyverhub_desktop")
        mqtt_layout.addRow("Client ID:", self.client_id_input)
        
        layout.addWidget(mqtt_group)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_btn)
        
        # Prefixes management
        prefix_group = QGroupBox("Device Prefixes")
        prefix_layout = QVBoxLayout(prefix_group)
        
        # Add prefix row
        add_row = QHBoxLayout()
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Enter prefix (e.g., MyDevices)")
        self.prefix_input.returnPressed.connect(self._add_prefix)  # Allow Enter key
        add_row.addWidget(self.prefix_input)
        
        self.add_prefix_btn = QPushButton("+")
        self.add_prefix_btn.setFixedWidth(40)
        self.add_prefix_btn.clicked.connect(self._add_prefix)
        self.add_prefix_btn.setEnabled(True)  # Always enabled
        add_row.addWidget(self.add_prefix_btn)
        
        prefix_layout.addLayout(add_row)
        
        # Prefix list
        self.prefix_list = QListWidget()
        self.prefix_list.setMaximumHeight(120)
        prefix_layout.addWidget(self.prefix_list)
        
        # Remove prefix button
        self.remove_prefix_btn = QPushButton("Remove Selected")
        self.remove_prefix_btn.clicked.connect(self._remove_prefix)
        self.remove_prefix_btn.setEnabled(False)
        self.remove_prefix_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        prefix_layout.addWidget(self.remove_prefix_btn)
        
        layout.addWidget(prefix_group)
        
        # Discover button
        self.discover_btn = QPushButton("🔍 Discover Devices")
        self.discover_btn.clicked.connect(self._discover_devices)
        self.discover_btn.setEnabled(False)
        layout.addWidget(self.discover_btn)
        
        # Spacer
        layout.addStretch()
        
        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        return panel
    
    def _create_devices_panel(self) -> QWidget:
        """Create the right devices panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("Devices")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Scrollable device container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_container)
        self.devices_layout.setSpacing(10)
        self.devices_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Placeholder when no devices
        self.no_devices_label = QLabel("No devices discovered.\nConnect to MQTT and add prefixes to discover devices.")
        self.no_devices_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_devices_label.setStyleSheet("color: #666666; padding: 50px;")
        self.devices_layout.addWidget(self.no_devices_label)
        
        scroll.setWidget(self.devices_container)
        layout.addWidget(scroll)
        
        return panel
    
    def _setup_connections(self):
        """Setup signal connections"""
        self.prefix_list.itemSelectionChanged.connect(
            lambda: self.remove_prefix_btn.setEnabled(bool(self.prefix_list.selectedItems()))
        )
    
    def _load_settings(self):
        """Load saved settings"""
        self.broker_input.setText(self.settings.value("broker", "test.mosquitto.org"))
        self.port_input.setValue(int(self.settings.value("port", 1883)))
        self.username_input.setText(self.settings.value("username", ""))
        self.password_input.setText(self.settings.value("password", ""))
        self.client_id_input.setText(self.settings.value("client_id", "gyverhub_desktop"))
        
        # Load prefixes
        prefixes = self.settings.value("prefixes", [])
        if isinstance(prefixes, list):
            for prefix in prefixes:
                self.prefix_list.addItem(prefix)
    
    def _save_settings(self):
        """Save current settings"""
        self.settings.setValue("broker", self.broker_input.text())
        self.settings.setValue("port", self.port_input.value())
        self.settings.setValue("username", self.username_input.text())
        self.settings.setValue("password", self.password_input.text())
        self.settings.setValue("client_id", self.client_id_input.text())
        
        # Save prefixes
        prefixes = [self.prefix_list.item(i).text() for i in range(self.prefix_list.count())]
        self.settings.setValue("prefixes", prefixes)
    
    def _log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_connect_clicked(self):
        """Handle connect/disconnect button click"""
        if self.mqtt_client and self.mqtt_client.connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """Connect to MQTT broker"""
        broker = self.broker_input.text().strip()
        if not broker:
            QMessageBox.warning(self, "Error", "Please enter a broker address")
            return
        
        config = MQTTConfig(
            broker=broker,
            port=self.port_input.value(),
            username=self.username_input.text() or None,
            password=self.password_input.text() or None,
            client_id=self.client_id_input.text() or "gyverhub_desktop"
        )
        
        self.mqtt_client = GyverHubMQTT(config)
        
        # Setup callbacks to emit signals (thread-safe)
        self.mqtt_client.on_connect = lambda success: self.mqtt_signals.connected.emit(success)
        self.mqtt_client.on_disconnect = lambda: self.mqtt_signals.disconnected.emit()
        self.mqtt_client.on_device_discovered = lambda device: self.mqtt_signals.device_discovered.emit(device)
        self.mqtt_client.on_button_ack = lambda dev_id, btn_id, prefix: self.mqtt_signals.button_ack.emit(dev_id, btn_id, prefix)
        self.mqtt_client.on_message = lambda msg: self.mqtt_signals.message_received.emit(msg)
        
        # Add existing prefixes
        for i in range(self.prefix_list.count()):
            prefix = self.prefix_list.item(i).text()
            self.mqtt_client.add_prefix(prefix)
        
        self._log(f"Connecting to {broker}:{config.port}...")
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        
        if not self.mqtt_client.connect():
            self._log("Connection failed!")
            self.connect_btn.setEnabled(True)
            self.connect_btn.setText("Connect")
            QMessageBox.critical(self, "Error", "Failed to connect to MQTT broker")
    
    def _disconnect(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        self._save_settings()
    
    @pyqtSlot(bool)
    def _on_mqtt_connected(self, success: bool):
        """Called when MQTT connection established (in Qt thread)"""
        if success:
            self._log("✓ Connected to MQTT broker")
            self.statusBar.showMessage("Connected")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setEnabled(True)
            self.discover_btn.setEnabled(True)
            
            # Auto-discover devices
            self._discover_devices()
        else:
            self._log("✗ Connection failed")
            self.connect_btn.setText("Connect")
            self.connect_btn.setEnabled(True)
    
    @pyqtSlot()
    def _on_mqtt_disconnected(self):
        """Called when MQTT connection lost (in Qt thread)"""
        self._log("Disconnected from MQTT broker")
        self.statusBar.showMessage("Disconnected")
        self.connect_btn.setText("Connect")
        self.connect_btn.setEnabled(True)
        self.discover_btn.setEnabled(False)
    
    @pyqtSlot(object)
    def _on_mqtt_message(self, msg: ParsedMessage):
        """Called for all parsed messages (in Qt thread)"""
        self._log(f"[{msg.msg_type.value}] {msg.device_id}")
    
    @pyqtSlot(object)
    def _on_device_discovered(self, device: Device):
        """Called when a new device is discovered (in Qt thread)"""
        self._log(f"✓ Device discovered: {device.name} ({device.platform})")
        
        # Hide "no devices" label
        self.no_devices_label.hide()
        
        # Create device widget
        if device.unique_id not in self.device_widgets:
            widget = DeviceWidget(device)
            widget.widget_changed.connect(self._on_widget_changed)
            widget.refresh_requested.connect(self._on_refresh_requested)
            
            self.devices_layout.addWidget(widget)
            self.device_widgets[device.unique_id] = widget
    
    @pyqtSlot(str, str, str)
    def _on_button_ack(self, device_id: str, button_id: str, prefix: str):
        """Called when button click is acknowledged (in Qt thread)"""
        unique_id = f"{prefix}_{device_id}"
        if unique_id in self.device_widgets:
            self.device_widgets[unique_id].flash_widget(button_id)
            self._log(f"✓ Widget '{button_id}' acknowledged")
    
    def _on_widget_changed(self, device_id: str, widget_id: str, value):
        """Handle widget interaction from device widget"""
        if not self.mqtt_client:
            return
        
        # Find the device
        for device in self.mqtt_client.device_manager.get_all_devices():
            if device.device_id == device_id:
                self._log(f"→ Setting widget '{widget_id}' to '{value}' on {device.name}")
                self.mqtt_client.set_widget_value(device, widget_id, value)
                break
    
    def _on_refresh_requested(self, device_id: str):
        """Handle UI refresh request from device widget"""
        if not self.mqtt_client:
            return
        
        # Find the device and request UI update
        for device in self.mqtt_client.device_manager.get_all_devices():
            if device.device_id == device_id:
                self.mqtt_client.request_ui(device)
                break
    
    def _add_prefix(self):
        """Add a new prefix to monitor"""
        prefix = self.prefix_input.text().strip()
        if not prefix:
            return
        
        # Check for duplicates
        for i in range(self.prefix_list.count()):
            if self.prefix_list.item(i).text() == prefix:
                QMessageBox.warning(self, "Duplicate", f"Prefix '{prefix}' already exists")
                return
        
        self.prefix_list.addItem(prefix)
        self.prefix_input.clear()
        
        # Add to MQTT client if connected
        if self.mqtt_client and self.mqtt_client.connected:
            self.mqtt_client.add_prefix(prefix)
            self._log(f"Added prefix: {prefix}")
            # Discover devices on new prefix
            self.mqtt_client.discover_devices(prefix)
        
        self._save_settings()
    
    def _remove_prefix(self):
        """Remove selected prefix"""
        items = self.prefix_list.selectedItems()
        if not items:
            return
        
        prefix = items[0].text()
        row = self.prefix_list.row(items[0])
        self.prefix_list.takeItem(row)
        
        # Remove from MQTT client
        if self.mqtt_client:
            self.mqtt_client.remove_prefix(prefix)
            self._log(f"Removed prefix: {prefix}")
        
        self._save_settings()
    
    def _discover_devices(self):
        """Send discovery request to all prefixes"""
        if not self.mqtt_client or not self.mqtt_client.connected:
            return
        
        if self.prefix_list.count() == 0:
            self._log("⚠ Add at least one prefix to discover devices")
            return
        
        self._log("Discovering devices...")
        self.mqtt_client.discover_devices()
    
    def closeEvent(self, event):
        """Handle window close"""
        self._save_settings()
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        event.accept()
