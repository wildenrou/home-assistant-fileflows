"""Constants for the FileFlows integration."""

DOMAIN = "fileflows"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_CONNECTED_LAST_SEEN_TIMESPAN = "connected_last_seen_timespan"

# Default values
DEFAULT_PORT = 8585  # Updated to match user's FileFlows setup
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_CONNECTED_LAST_SEEN_TIMESPAN = 5  # 5 minutes

# Sensor types
SENSOR_TYPES = {
    "status": {
        "name": "Status",
        "icon": "mdi:server",
        "device_class": None,
        "key": "status",
    },
    "queue_count": {
        "name": "Queue Count", 
        "icon": "mdi:format-list-numbered",
        "device_class": None,
        "key": "queue_count",
    },
    "processing_count": {
        "name": "Processing Count",
        "icon": "mdi:cog",
        "device_class": None,
        "key": "processing_count",
    },
    "worker_count": {
        "name": "Worker Count",
        "icon": "mdi:worker",
        "device_class": None,
        "key": "worker_count",
    },
}
