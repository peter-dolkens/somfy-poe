# Somfy PoE Motors - Home Assistant Integration

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-blue)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A native Home Assistant custom integration for **local control** of Somfy PoE (Power over Ethernet) motors. This integration provides automatic discovery, secure communication, and full control of your Somfy motorized blinds, shades, and screens.

## Features

✨ **Automatic Discovery**: Uses mDNS/Bonjour to automatically find motors on your network
🔒 **Secure Communication**: Full TLS and AES-128 encryption support
🏠 **Native Integration**: Each motor appears as a separate device in Home Assistant
🎛️ **Full Control**: Open, close, stop, and position control
📊 **Real-time Status**: Current position, direction, and motor status
🔄 **Automatic Reconnection**: Handles network interruptions gracefully
🎯 **Identify Motors**: Wink service to identify physical motors
⚙️ **Config Flow UI**: Easy setup through Home Assistant UI

## Requirements

### Hardware
- Somfy Sonesse 30 or 40 PoE motors
- PoE+ (IEEE 802.3at) capable switch
- Home Assistant installation (on same network as motors)

### Software
- Home Assistant 2023.1 or newer
- Python 3.10 or newer (included with Home Assistant)

### Network
- Motors and Home Assistant on same network/VLAN
- mDNS/multicast enabled on network (for discovery)
- Ports 55055 (UDP) and 55056 (TCP) accessible

## Installation

### HACS (Recommended)

1. **Open HACS** in Home Assistant
2. Click the **3 dots** in the top right corner
3. Select **Custom repositories**
4. Add repository URL: `https://github.com/yourusername/somfy-poe`
5. Category: **Integration**
6. Click **Install**
7. Restart Home Assistant

### Manual Installation

1. **Download** the `custom_components/somfy_poe` directory
2. **Copy** it to your Home Assistant `custom_components` directory:
   ```
   <config_directory>/custom_components/somfy_poe/
   ```
3. **Restart** Home Assistant

## Quick Start

### Automatic Setup (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Somfy PoE Motors**
4. Select **Automatic discovery**
5. Wait for discovery (10 seconds)
6. Select your motor from the list
7. Enter the **4-digit PIN** (printed on motor label)
8. Click **Submit**

✅ Done! Your motor will appear as a new device with a cover entity.

### Manual Setup

If automatic discovery doesn't work:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Somfy PoE Motors**
4. Select **Manual configuration**
5. Enter motor **IP address**
6. Enter **4-digit PIN** (from motor label)
7. Click **Submit**

## Configuration

### Finding Your Motor's IP Address

**Method 1: Router/DHCP**
- Check your router's DHCP client list
- Look for hostname: `sfy_poe_XXXXXX.local`

**Method 2: Network Scanner**
- Use a network scanner (e.g., Fing, Angry IP Scanner)
- Look for devices on ports 55055-55056

**Method 3: Somfy Config Tool**
- Use the official Somfy PoE Config Tool
- Note the IP address shown

### Finding Your Motor's PIN

The 4-digit PIN code is printed on the motor label. **Do not lose this label!** The PIN cannot be recovered if lost.

## Usage

### Basic Control

The integration creates a Cover entity for each motor:

```yaml
# In automations or scripts
service: cover.open_cover
target:
  entity_id: cover.living_room_blind

service: cover.close_cover
target:
  entity_id: cover.living_room_blind

service: cover.stop_cover
target:
  entity_id: cover.living_room_blind

service: cover.set_cover_position
target:
  entity_id: cover.living_room_blind
data:
  position: 50  # 0=closed, 100=open
```

### Identify Motor (Wink)

Make the motor jog to identify which physical motor it is:

```yaml
service: somfy_poe.wink
target:
  entity_id: cover.living_room_blind
```

### Advanced Automations

**Close blinds at sunset:**
```yaml
automation:
  - alias: "Close blinds at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: cover.close_cover
        target:
          entity_id: cover.living_room_blind
```

**Open to 50% in the morning:**
```yaml
automation:
  - alias: "Partial open morning"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: cover.set_cover_position
        target:
          entity_id: cover.living_room_blind
        data:
          position: 50
```

**Stop if obstacle detected:**
```yaml
automation:
  - alias: "Stop on obstacle"
    trigger:
      - platform: state
        entity_id: cover.living_room_blind
        attribute: status
        to: "obstacle"
    action:
      - service: cover.stop_cover
        target:
          entity_id: cover.living_room_blind
      - service: notify.mobile_app
        data:
          message: "Blind obstacle detected!"
```

## Entity Attributes

Each cover entity provides these attributes:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `position` | Current position (0-100) | `45.2` |
| `direction` | Movement direction | `up`, `down`, `stopped` |
| `status` | Motor status | `ok`, `obstacle`, `thermal` |
| `target_id` | Motor unique ID | `4CC206:160D00` |
| `firmware` | Firmware version | `1.2.0` |
| `model` | Motor model | `Sonesse 30 PoE` |
| `mac` | MAC address | `4C:C2:06:16:0D:00` |

Access in templates:
```yaml
{{ state_attr('cover.living_room_blind', 'direction') }}
{{ state_attr('cover.living_room_blind', 'firmware') }}
```

## Troubleshooting

### Discovery Not Finding Motors

**Check mDNS:**
- Ensure your network supports multicast/mDNS
- Some routers/VLANs block multicast traffic
- Try manual configuration instead

**Network Issues:**
- Verify motors are powered (check PoE switch)
- Ensure Home Assistant and motors are on same network
- Check firewall rules for ports 5353 (mDNS), 55055, 55056

**Test manually:**
```bash
# From Home Assistant host
ping sfy_poe_160d00.local
```

### Authentication Failed

- Verify PIN code (check motor label)
- PIN is case-sensitive and must be 4 digits
- Ensure motor hasn't been factory reset

### Connection Issues

**Motor not responding:**
- Check motor has power (PoE LED should be lit)
- Verify IP address is correct
- Try power cycling the motor
- Check network connectivity

**Frequent disconnections:**
- Check network stability
- Verify PoE switch provides adequate power (PoE+ / 30W)
- Check for network congestion
- Consider using a static IP or DHCP reservation

### Position Not Updating

- Check motor is responding (try manual control)
- Verify network connectivity
- Restart Home Assistant
- Check logs for errors

### Logs

Enable debug logging:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.somfy_poe: debug
```

View logs:
- **Settings** → **System** → **Logs**
- Look for `custom_components.somfy_poe` entries

## Multiple Motors

To add multiple motors:

1. Repeat the setup process for each motor
2. Each motor will appear as a separate device
3. You can rename entities in Home Assistant UI

**Group control:**
```yaml
# configuration.yaml
cover:
  - platform: group
    name: "All Living Room Blinds"
    entities:
      - cover.living_room_blind_1
      - cover.living_room_blind_2
      - cover.living_room_blind_3
```

## Uninstallation

1. **Remove integration**:
   - Go to **Settings** → **Devices & Services**
   - Find **Somfy PoE Motors** integration
   - Click **3 dots** → **Delete**

2. **Remove files** (if not using HACS):
   - Delete `custom_components/somfy_poe/`
   - Restart Home Assistant

## Architecture

```
┌─────────────────────────────────────────┐
│         Home Assistant                  │
│  ┌───────────────────────────────────┐ │
│  │  Somfy PoE Integration            │ │
│  │  - Config Flow (UI setup)         │ │
│  │  - mDNS Discovery                 │ │
│  │  - Cover Platform                 │ │
│  │  - Data Coordinator               │ │
│  └───────────┬───────────────────────┘ │
└──────────────┼─────────────────────────┘
               │
               ├─ TCP/TLS (Auth) Port 55056
               └─ UDP/AES (Commands) Port 55055
               │
┌──────────────┼─────────────────────────┐
│  Somfy PoE Motor                        │
│  - Authentication                       │
│  - Position Control                     │
│  - Status Reporting                     │
└─────────────────────────────────────────┘
```

## Security Considerations

- **Local Control**: All communication is local, no cloud required
- **Encryption**: TLS for authentication, AES-128 for commands
- **PIN Protection**: Each motor requires unique PIN
- **Network Security**: Keep motors on isolated VLAN if possible
- **Certificate Validation**: Disabled by default (motors use self-signed certs)

## Known Limitations

- Certificate validation is disabled (motors use self-signed certificates)
- No push notifications from motors (polling only)
- Maximum 1 connection per motor (integration maintains single connection)
- Group commands not supported (use Home Assistant groups instead)

## FAQ

**Q: Do motors need internet access?**
A: No, this integration uses local control only.

**Q: Can I use this with Somfy Tahoma/MyLink?**
A: No, this is specifically for PoE motors. Tahoma/MyLink use different protocols.

**Q: Will this void my warranty?**
A: This uses the documented API. Check with Somfy for warranty details.

**Q: Can I control motors from outside my network?**
A: Yes, through Home Assistant's remote access (Nabu Casa or your own setup).

**Q: How many motors can I control?**
A: No hard limit. Each motor uses minimal resources.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/somfy-poe/issues)
- **Documentation**: [Full API Documentation](../../SOMFY_POE_API_DOCUMENTATION.md)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/somfy-poe/discussions)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](../../CONTRIBUTING.md) first.

## License

This integration is provided for educational and interoperability purposes.

**Disclaimer**: This is an unofficial integration based on reverse engineering. Somfy®, Sonesse®, and related trademarks are property of Somfy Systems, Inc. Use at your own risk.

## Acknowledgments

- Based on analysis of Somfy PoE Motor driver
- Thanks to the Home Assistant community
- Inspired by other local control integrations

---

**Version**: 1.0.0
**Last Updated**: January 2026
**Home Assistant Version**: 2023.1+
