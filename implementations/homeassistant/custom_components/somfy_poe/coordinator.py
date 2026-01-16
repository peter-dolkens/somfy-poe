"""DataUpdateCoordinator for Somfy PoE."""
import logging
from datetime import timedelta
from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_HOST

from .const import DOMAIN, CONF_PIN, UPDATE_INTERVAL
from .motor import SomfyPoEMotorController

_LOGGER = logging.getLogger(__name__)


class SomfyPoECoordinator(DataUpdateCoordinator):
    """Class to manage fetching Somfy PoE motor data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.motor = SomfyPoEMotorController(
            host=entry.data[CONF_HOST],
            pin=entry.data[CONF_PIN],
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the motor."""
        # Ensure connection
        if not self.motor.is_connected:
            _LOGGER.debug("Connecting to motor...")
            connected = await self.motor.connect()
            if not connected:
                raise UpdateFailed("Failed to connect to motor")

        # Fetch position and status
        position_data = await self.motor.get_position()
        if position_data is None:
            # Try to reconnect
            _LOGGER.warning("Failed to get position, attempting reconnect")
            await self.motor.disconnect()
            connected = await self.motor.connect()
            if not connected:
                raise UpdateFailed("Lost connection to motor")
            position_data = await self.motor.get_position()
            if position_data is None:
                raise UpdateFailed("Failed to get position data")

        return position_data

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        await self.motor.disconnect()

    async def async_move_up(self) -> bool:
        """Move motor up."""
        result = await self.motor.move_up()
        if result:
            await self.async_request_refresh()
        return result

    async def async_move_down(self) -> bool:
        """Move motor down."""
        result = await self.motor.move_down()
        if result:
            await self.async_request_refresh()
        return result

    async def async_stop(self) -> bool:
        """Stop motor."""
        result = await self.motor.stop()
        if result:
            await self.async_request_refresh()
        return result

    async def async_move_to_position(self, position: float) -> bool:
        """Move motor to position."""
        result = await self.motor.move_to_position(position)
        if result:
            await self.async_request_refresh()
        return result

    async def async_wink(self) -> bool:
        """Make motor wink."""
        return await self.motor.wink()

    async def async_get_info(self) -> Dict[str, Any]:
        """Get motor info."""
        return await self.motor.get_info()
