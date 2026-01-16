"""Config flow for Somfy PoE integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_PIN
from .discovery import async_discover_motors, SomfyPoEMotor
from .motor import SomfyPoEMotorController

_LOGGER = logging.getLogger(__name__)


class SomfyPoEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Somfy PoE."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_motors: Dict[str, SomfyPoEMotor] = {}
        self._selected_motor: Optional[SomfyPoEMotor] = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check if user wants to discover or manually configure
            if user_input.get("discovery_mode") == "auto":
                return await self.async_step_discovery()
            else:
                return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("discovery_mode", default="auto"): vol.In(
                        {
                            "auto": "Automatic discovery (recommended)",
                            "manual": "Manual configuration",
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_discovery(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle discovery step."""
        if user_input is not None:
            # Check if user wants to try manual instead
            if user_input.get("manual_fallback"):
                return await self.async_step_manual()

            # User selected a motor
            motor_id = user_input["motor"]
            self._selected_motor = self._discovered_motors[motor_id]
            return await self.async_step_auth()

        # Perform discovery
        _LOGGER.info("Starting motor discovery...")
        motors = await async_discover_motors(timeout=10)

        if not motors:
            _LOGGER.warning("No motors discovered")
            # Offer manual configuration instead of aborting
            return await self.async_step_discovery_failed()

        # Store discovered motors
        self._discovered_motors = {motor.target_id: motor for motor in motors}

        # Create selection options
        motor_options = {
            motor.target_id: f"{motor.motor_name} ({motor.ip_address})"
            for motor in motors
        }

        return self.async_show_form(
            step_id="discovery",
            data_schema=vol.Schema(
                {
                    vol.Required("motor"): vol.In(motor_options),
                }
            ),
            description_placeholders={
                "count": str(len(motors)),
            },
        )

    async def async_step_discovery_failed(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle discovery failure - offer manual configuration."""
        if user_input is not None:
            if user_input.get("try_manual"):
                return await self.async_step_manual()
            else:
                return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="discovery_failed",
            data_schema=vol.Schema(
                {
                    vol.Required("try_manual", default=True): bool,
                }
            ),
        )

    async def async_step_manual(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle manual configuration step."""
        errors = {}

        if user_input is not None:
            # Validate the input
            host = user_input[CONF_HOST]
            pin = user_input[CONF_PIN]

            # Try to connect and authenticate
            motor = SomfyPoEMotorController(host=host, pin=pin)
            connected = await motor.connect()

            if connected:
                # Get motor info
                info = await motor.get_info()
                await motor.disconnect()

                motor_name = info.get("name", "Somfy Blind") if info else "Somfy Blind"

                # Create entry
                return self.async_create_entry(
                    title=motor_name,
                    data={
                        CONF_HOST: host,
                        CONF_PIN: pin,
                        CONF_NAME: motor_name,
                    },
                )
            else:
                errors["base"] = "cannot_connect"
                await motor.disconnect()

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PIN): str,
                }
            ),
            errors=errors,
        )

    async def async_step_auth(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle authentication step for discovered motor."""
        errors = {}

        if user_input is not None:
            pin = user_input[CONF_PIN]

            # Try to connect and authenticate
            motor = SomfyPoEMotorController(
                host=self._selected_motor.ip_address,
                pin=pin,
            )
            connected = await motor.connect()

            if connected:
                await motor.disconnect()

                # Create entry
                return self.async_create_entry(
                    title=self._selected_motor.motor_name,
                    data={
                        CONF_HOST: self._selected_motor.ip_address,
                        CONF_PIN: pin,
                        CONF_NAME: self._selected_motor.motor_name,
                    },
                )
            else:
                errors["base"] = "invalid_auth"
                await motor.disconnect()

        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PIN): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "motor_name": self._selected_motor.motor_name,
                "ip_address": self._selected_motor.ip_address,
            },
        )

    async def async_step_zeroconf(
        self, discovery_info: Dict[str, Any]
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.info("Discovered motor via zeroconf: %s", discovery_info)

        # Extract motor information
        properties = discovery_info.get("properties", {})
        target_id = properties.get("targetid")
        motor_name = properties.get("name", "Somfy Blind")
        ip_address = discovery_info.get("host")

        if not target_id or not ip_address:
            return self.async_abort(reason="invalid_discovery_info")

        # Check if already configured
        await self.async_set_unique_id(target_id)
        self._abort_if_unique_id_configured()

        # Store discovered motor info
        self._selected_motor = SomfyPoEMotor(
            name=discovery_info.get("name", ""),
            hostname=discovery_info.get("hostname", ""),
            ip_address=ip_address,
            port=discovery_info.get("port", 55056),
            properties=properties,
        )

        # Show confirmation form
        self.context["title_placeholders"] = {"name": motor_name}
        return await self.async_step_auth()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SomfyPoEOptionsFlowHandler(config_entry)


class SomfyPoEOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Somfy PoE."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "update_interval",
                        default=self.config_entry.options.get("update_interval", 5),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                }
            ),
        )
