"""Constants for GyverHub integration."""
from typing import Final

DOMAIN: Final = "gyverhub"

# Configuration keys
CONF_PREFIX: Final = "prefix"
CONF_PREFIXES: Final = "prefixes"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# Default values
DEFAULT_PREFIX: Final = "MyDevices"
DEFAULT_CLIENT_ID: Final = "gyverhub_ha"
DEFAULT_UPDATE_INTERVAL: Final = 0.5  # seconds

# MQTT topic patterns
TOPIC_DISCOVER: Final = "{prefix}"
TOPIC_HUB: Final = "{prefix}/hub/#"
TOPIC_UI: Final = "{prefix}/{device_id}/{client_id}/ui"
TOPIC_SET: Final = "{prefix}/{device_id}/{client_id}/set/{widget_name}"
TOPIC_PING: Final = "{prefix}/{device_id}/{client_id}/ping"

# Button click payload
BUTTON_CLICK_PAYLOAD: Final = "2"

# Device info
ATTR_DEVICE_ID: Final = "device_id"
ATTR_PREFIX: Final = "prefix"
ATTR_PLATFORM: Final = "platform"
ATTR_VERSION: Final = "version"
ATTR_ICON: Final = "icon"

# Signal events
SIGNAL_DEVICE_DISCOVERED: Final = f"{DOMAIN}_device_discovered"
SIGNAL_DEVICE_UI_UPDATED: Final = f"{DOMAIN}_device_ui_updated"
