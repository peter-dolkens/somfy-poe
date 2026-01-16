"""Cover platform for Somfy PoE integration."""
import logging
from typing import Any, Optional

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (
    DOMAIN,
    ATTR_POSITION,
    ATTR_DIRECTION,
    ATTR_STATUS,
    ATTR_TARGET_ID,
    ATTR_FIRMWARE,
    ATTR_MODEL,
    ATTR_MAC,
    POSITION_OPEN,
    POSITION_CLOSED,
    DIRECTION_UP,
    DIRECTION_DOWN,
    DIRECTION_STOPPED,
)
from .coordinator import SomfyPoECoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Somfy PoE cover from a config entry."""
    coordinator: SomfyPoECoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get motor info for device details
    motor_info = await coordinator.async_get_info()

    async_add_entities([SomfyPoECover(coordinator, entry, motor_info)], True)


class SomfyPoECover(CoordinatorEntity, CoverEntity):
    """Representation of a Somfy PoE cover."""

    _attr_has_entity_name = True
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        coordinator: SomfyPoECoordinator,
        entry: ConfigEntry,
        motor_info: Optional[dict],
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)

        self._entry = entry
        self._motor_info = motor_info or {}

        # Entity attributes
        self._attr_unique_id = coordinator.motor.target_id
        self._attr_name = entry.data.get(CONF_NAME, "Somfy Blind")

        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.motor.target_id)},
            "name": self._attr_name,
            "manufacturer": "Somfy",
            "model": self._motor_info.get("model", "PoE Motor"),
            "sw_version": self._motor_info.get("firmware", "Unknown"),
            "hw_version": self._motor_info.get("hardware", "Unknown"),
            "configuration_url": f"https://{entry.data[CONF_HOST]}:55056",
        }

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover (0=closed, 100=open)."""
        if self.coordinator.data:
            # Somfy uses 0=open, 100=closed
            # Home Assistant uses 0=closed, 100=open
            # So we need to invert
            position = self.coordinator.data.get("value")
            if position is not None:
                return int(100 - position)
        return None

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed."""
        position = self.current_cover_position
        if position is not None:
            return position == 0
        return None

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        if self.coordinator.data:
            direction = self.coordinator.data.get("direction")
            # Motor moving up = opening (position decreasing in Somfy terms)
            return direction == DIRECTION_UP
        return False

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        if self.coordinator.data:
            direction = self.coordinator.data.get("direction")
            # Motor moving down = closing (position increasing in Somfy terms)
            return direction == DIRECTION_DOWN
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}

        if self.coordinator.data:
            attributes[ATTR_DIRECTION] = self.coordinator.data.get("direction")
            attributes[ATTR_STATUS] = self.coordinator.data.get("status")

        if self.coordinator.motor.target_id:
            attributes[ATTR_TARGET_ID] = self.coordinator.motor.target_id

        if self._motor_info:
            if "firmware" in self._motor_info:
                attributes[ATTR_FIRMWARE] = self._motor_info["firmware"]
            if "model" in self._motor_info:
                attributes[ATTR_MODEL] = self._motor_info["model"]
            if "mac" in self._motor_info:
                attributes[ATTR_MAC] = self._motor_info["mac"]

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.motor.is_connected

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.async_move_up()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.async_move_down()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.coordinator.async_stop()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        # Home Assistant: 0=closed, 100=open
        # Somfy: 0=open, 100=closed
        # So we need to invert
        ha_position = kwargs.get("position")
        somfy_position = 100 - ha_position
        await self.coordinator.async_move_to_position(somfy_position)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        # Register services
        platform = self.platform
        platform.async_register_entity_service(
            "wink",
            {},
            "async_wink",
        )

    async def async_wink(self) -> None:
        """Make the motor wink to identify it."""
        await self.coordinator.async_wink()
