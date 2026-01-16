#!/usr/bin/env python3
"""
Test script to verify connection to Somfy PoE motors.
Run this before installing the Home Assistant integration to verify your motor works.

Usage:
    python3 test_connection.py <motor_ip> <pin>

Example:
    python3 test_connection.py 192.168.1.150 1234
"""

import sys
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check dependencies
try:
    from zeroconf import Zeroconf, ServiceBrowser
    from Crypto.Cipher import AES
except ImportError:
    logger.error("Missing dependencies. Install with:")
    logger.error("pip install zeroconf pycryptodome")
    sys.exit(1)

# Import the motor controller
try:
    sys.path.insert(0, 'custom_components/somfy_poe')
    from motor import SomfyPoEMotorController
    from discovery import async_discover_motors
except ImportError:
    logger.error("Could not import integration modules.")
    logger.error("Make sure you're running this from the homeassistant/ directory")
    sys.exit(1)


async def test_discovery():
    """Test motor discovery."""
    logger.info("=" * 60)
    logger.info("Testing Motor Discovery")
    logger.info("=" * 60)

    logger.info("Scanning network for Somfy PoE motors (10 seconds)...")
    motors = await async_discover_motors(timeout=10)

    if not motors:
        logger.warning("No motors found via discovery")
        return None

    logger.info(f"Found {len(motors)} motor(s):")
    for motor in motors:
        logger.info(f"  - {motor.motor_name}")
        logger.info(f"    IP: {motor.ip_address}")
        logger.info(f"    Target ID: {motor.target_id}")
        logger.info(f"    Model: {motor.model}")
        logger.info(f"    Firmware: {motor.firmware}")
        logger.info("")

    return motors[0] if motors else None


async def test_connection(ip: str, pin: str):
    """Test connection to a specific motor."""
    logger.info("=" * 60)
    logger.info("Testing Motor Connection")
    logger.info("=" * 60)
    logger.info(f"Motor IP: {ip}")
    logger.info(f"PIN: {pin}")
    logger.info("")

    # Create controller
    motor = SomfyPoEMotorController(host=ip, pin=pin)

    # Test connection
    logger.info("Connecting to motor...")
    connected = await motor.connect()

    if not connected:
        logger.error("Failed to connect to motor!")
        logger.error("Check:")
        logger.error("  - Motor is powered and accessible")
        logger.error("  - IP address is correct")
        logger.error("  - PIN is correct")
        logger.error("  - Firewall allows ports 55055-55056")
        return False

    logger.info("✓ Connection successful!")
    logger.info(f"  Target ID: {motor.target_id}")
    logger.info("")

    # Get motor info
    logger.info("Getting motor information...")
    info = await motor.get_info()

    if info:
        logger.info("✓ Motor Information:")
        logger.info(f"  Name: {info.get('name', 'Unknown')}")
        logger.info(f"  Model: {info.get('model', 'Unknown')}")
        logger.info(f"  Firmware: {info.get('firmware', 'Unknown')}")
        logger.info(f"  Hardware: {info.get('hardware', 'Unknown')}")
        logger.info(f"  MAC: {info.get('mac', 'Unknown')}")
        logger.info(f"  Hostname: {info.get('hostname', 'Unknown')}")
        logger.info("")
    else:
        logger.warning("Could not get motor info")

    # Get position
    logger.info("Getting current position...")
    position = await motor.get_position()

    if position:
        logger.info("✓ Current Position:")
        logger.info(f"  Position: {position.get('value', 'Unknown')}%")
        logger.info(f"  Direction: {position.get('direction', 'Unknown')}")
        logger.info(f"  Status: {position.get('status', 'Unknown')}")
        logger.info("")
    else:
        logger.warning("Could not get position")

    # Test wink
    logger.info("Testing wink (motor should jog)...")
    wink_ok = await motor.wink()

    if wink_ok:
        logger.info("✓ Wink successful - did the motor jog?")
        logger.info("")
    else:
        logger.warning("Wink command failed")

    # Cleanup
    await motor.disconnect()
    logger.info("Disconnected from motor")

    return True


async def interactive_test():
    """Interactive test with discovery."""
    logger.info("=" * 60)
    logger.info("Somfy PoE Motor Connection Test")
    logger.info("=" * 60)
    logger.info("")

    # Try discovery first
    motor = await test_discovery()

    if motor:
        print("\nWould you like to test this motor? (y/n): ", end='')
        response = input().strip().lower()

        if response == 'y':
            print("Enter PIN code: ", end='')
            pin = input().strip()
            await test_connection(motor.ip_address, pin)
    else:
        print("\nEnter motor IP address: ", end='')
        ip = input().strip()
        print("Enter PIN code: ", end='')
        pin = input().strip()
        await test_connection(ip, pin)


async def main():
    """Main function."""
    if len(sys.argv) == 3:
        # Command line arguments provided
        ip = sys.argv[1]
        pin = sys.argv[2]
        success = await test_connection(ip, pin)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        try:
            await interactive_test()
        except KeyboardInterrupt:
            logger.info("\nTest cancelled by user")
            sys.exit(1)

    logger.info("=" * 60)
    logger.info("Test Complete")
    logger.info("=" * 60)
    logger.info("")
    logger.info("If all tests passed, you can now install the integration")
    logger.info("in Home Assistant and add your motor!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("Test failed with exception:")
        sys.exit(1)
