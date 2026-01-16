"""mDNS discovery for Somfy PoE motors."""
import logging
import socket
from typing import List, Dict, Optional

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

from .const import MDNS_TYPE

_LOGGER = logging.getLogger(__name__)


class SomfyPoEMotor:
    """Represents a discovered Somfy PoE motor."""

    def __init__(
        self,
        name: str,
        hostname: str,
        ip_address: str,
        port: int,
        properties: Dict[str, str],
    ):
        """Initialize motor info."""
        self.name = name
        self.hostname = hostname
        self.ip_address = ip_address
        self.port = port
        self.properties = properties

    @property
    def target_id(self) -> Optional[str]:
        """Return the motor target ID."""
        return self.properties.get("targetid")

    @property
    def mac(self) -> Optional[str]:
        """Return the motor MAC address."""
        return self.properties.get("mac")

    @property
    def model(self) -> Optional[str]:
        """Return the motor model."""
        return self.properties.get("model")

    @property
    def firmware(self) -> Optional[str]:
        """Return the firmware version."""
        return self.properties.get("firmware")

    @property
    def motor_name(self) -> Optional[str]:
        """Return the user-assigned motor name."""
        return self.properties.get("name", "Unnamed Motor")

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SomfyPoEMotor(name={self.motor_name}, "
            f"target_id={self.target_id}, ip={self.ip_address})"
        )


class SomfyPoEDiscovery(ServiceListener):
    """Service listener for discovering Somfy PoE motors."""

    def __init__(self):
        """Initialize the discovery listener."""
        self.motors: Dict[str, SomfyPoEMotor] = {}
        self.zeroconf: Optional[Zeroconf] = None
        self.browser: Optional[ServiceBrowser] = None

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is discovered."""
        info = zc.get_service_info(type_, name)
        if info:
            self._process_service_info(name, info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        if name in self.motors:
            _LOGGER.info("Motor removed: %s", name)
            del self.motors[name]

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        info = zc.get_service_info(type_, name)
        if info:
            _LOGGER.debug("Motor updated: %s", name)
            self._process_service_info(name, info)

    def _process_service_info(self, name: str, info: ServiceInfo) -> None:
        """Process discovered service information."""
        try:
            # Extract IP addresses
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            if not addresses:
                _LOGGER.warning("No IP addresses found for %s", name)
                return

            ip_address = addresses[0]

            # Parse TXT record properties
            properties = {}
            if info.properties:
                for key, value in info.properties.items():
                    try:
                        properties[key.decode("utf-8")] = value.decode("utf-8")
                    except (UnicodeDecodeError, AttributeError):
                        _LOGGER.warning("Failed to decode property: %s", key)

            motor = SomfyPoEMotor(
                name=name,
                hostname=info.server,
                ip_address=ip_address,
                port=info.port,
                properties=properties,
            )

            self.motors[name] = motor

            _LOGGER.info(
                "Discovered motor: %s (IP: %s, Target ID: %s)",
                motor.motor_name,
                ip_address,
                motor.target_id,
            )

        except Exception as err:
            _LOGGER.exception("Error processing service info for %s: %s", name, err)

    def start_discovery(self) -> None:
        """Start the mDNS discovery process."""
        _LOGGER.info("Starting Somfy PoE motor discovery")
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, MDNS_TYPE, self)

    def stop_discovery(self) -> None:
        """Stop the mDNS discovery process."""
        if self.browser:
            self.browser.cancel()
            self.browser = None

        if self.zeroconf:
            self.zeroconf.close()
            self.zeroconf = None

        _LOGGER.info("Stopped Somfy PoE motor discovery")

    def get_motors(self) -> List[SomfyPoEMotor]:
        """Return list of discovered motors."""
        return list(self.motors.values())

    def get_motor_by_target_id(self, target_id: str) -> Optional[SomfyPoEMotor]:
        """Get a motor by its target ID."""
        for motor in self.motors.values():
            if motor.target_id == target_id:
                return motor
        return None


async def async_discover_motors(timeout: int = 10) -> List[SomfyPoEMotor]:
    """
    Discover Somfy PoE motors on the network.

    Args:
        timeout: Discovery duration in seconds

    Returns:
        List of discovered motors
    """
    import asyncio

    discovery = SomfyPoEDiscovery()
    discovery.start_discovery()

    try:
        await asyncio.sleep(timeout)
    finally:
        discovery.stop_discovery()

    return discovery.get_motors()
