"""Constants for the Somfy PoE integration."""

DOMAIN = "somfy_poe"

# Configuration constants
CONF_PIN = "pin"
CONF_TARGET_ID = "target_id"

# Network constants
TCP_PORT = 55056
UDP_PORT = 55055

# Discovery constants
MDNS_TYPE = "_somfy-poe._tcp.local."

# Update intervals
UPDATE_INTERVAL = 5  # seconds

# Attributes
ATTR_POSITION = "position"
ATTR_DIRECTION = "direction"
ATTR_STATUS = "status"
ATTR_TARGET_ID = "target_id"
ATTR_FIRMWARE = "firmware"
ATTR_MODEL = "model"
ATTR_MAC = "mac"

# Position encoding (Somfy protocol)
POSITION_OPEN = 0
POSITION_CLOSED = 100

# Motor status values
STATUS_OK = "ok"
STATUS_OBSTACLE = "obstacle"
STATUS_THERMAL = "thermal"

# Direction values
DIRECTION_UP = "up"
DIRECTION_DOWN = "down"
DIRECTION_STOPPED = "stopped"
