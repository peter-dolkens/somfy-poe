# ESPHome Somfy PoE - Feature List

## Current Features ✅

### Core Functionality

- ✅ **Full Protocol Implementation**
  - TLS/SSL authentication over TCP (port 55056)
  - AES-128-CBC encryption for UDP (port 55055)
  - PIN-based authentication
  - Session key exchange

- ✅ **Motor Control**
  - Open (move to upper limit)
  - Close (move to lower limit)
  - Stop (halt movement)
  - Position control (0-100%)
  - Wink/identify motor

- ✅ **Position Tracking**
  - Real-time position updates (0-100%)
  - Movement status (stopped/up/down)
  - Configurable polling interval

- ✅ **Connection Management**
  - Automatic connection on boot
  - Auto-reconnect after network issues
  - Manual reconnect button
  - Connection status monitoring

### Home Assistant Integration

- ✅ **Native Cover Entity**
  - Appears as standard Home Assistant cover
  - Full position control
  - Status display
  - Automation support

- ✅ **ESPHome API**
  - Encrypted communication
  - Real-time updates
  - Over-the-air updates
  - Config validation

- ✅ **Additional Entities**
  - Position sensor (percentage)
  - Status text sensor
  - Control buttons (wink, reconnect)

### Security

- ✅ **TLS Encryption**
  - Secure TCP connection to motor
  - Certificate exchange (motor self-signed)
  - Configurable certificate validation

- ✅ **AES Encryption**
  - All UDP commands encrypted
  - Random IV per message
  - PKCS7 padding

- ✅ **Secure Configuration**
  - Secrets file support
  - No hardcoded credentials
  - PIN protection

### User Experience

- ✅ **Easy Configuration**
  - YAML-based setup
  - Clear documentation
  - Example configurations

- ✅ **Detailed Logging**
  - Connection status
  - Command execution
  - Error reporting
  - Debug mode available

- ✅ **Error Handling**
  - Graceful connection failures
  - Authentication retry logic
  - UDP timeout handling
  - Motor error reporting

## Planned Features 🚧

### High Priority

- 🔲 **mDNS Auto-Discovery**
  - Automatic motor detection
  - No manual IP configuration
  - Hostname resolution support

- 🔲 **Heartbeat Implementation**
  - Keep TCP connection alive
  - Periodic ping to motor
  - Connection health monitoring

- 🔲 **Enhanced Error Reporting**
  - Detailed error messages to HA
  - Connection quality indicator
  - Motor status sensors (temp, errors)

- 🔲 **Position Update Optimization**
  - Push notifications from motor
  - Reduced polling frequency
  - Event-driven updates

### Medium Priority

- 🔲 **Multiple Motor Support**
  - Control multiple motors from one ESP32
  - Unified management
  - Group synchronization

- 🔲 **Group Control**
  - Send commands to motor groups
  - Synchronized movement
  - Group status tracking

- 🔲 **Preset Positions**
  - Use motor's 16 intermediate positions
  - Named presets in HA
  - Quick access buttons

- 🔲 **Configuration UI**
  - Web-based setup wizard
  - Motor discovery interface
  - Test controls

### Low Priority

- 🔲 **Advanced Motor Settings**
  - Speed configuration
  - Ramp settings (soft start/stop)
  - LED control
  - Network settings

- 🔲 **Lock State Management**
  - Motor lock/unlock
  - Priority control
  - Lock status display

- 🔲 **Firmware Management**
  - Motor firmware version display
  - Update notifications
  - Configuration backup/restore

- 🔲 **Statistics & Monitoring**
  - Movement counter
  - Runtime statistics
  - Error history
  - Performance metrics

## Feature Comparison

### vs. Somfy Official App

| Feature | ESPHome | Somfy App |
|---------|---------|-----------|
| Open/Close | ✅ | ✅ |
| Position Control | ✅ | ✅ |
| Home Assistant | ✅ | ❌ |
| Local Control | ✅ | ✅ |
| Cloud Required | ❌ | ❌ |
| Automation | ✅ | Limited |
| Multi-vendor | ✅ | ❌ |
| Cost | Free | Free |
| Motor Config | ❌ | ✅ |
| Limit Setup | ❌ | ✅ |

### vs. Driver

| Feature | ESPHome | Driver |
|---------|---------|------------|
| Protocol | Same | Same |
| Platform | ESP32 | System |
| Open Source | ✅ | ❌ |
| Cost | ~$10 | $$$$ |
| Home Assistant | ✅ | Via Bridge |
| Easy Setup | ✅ | Complex |
| Updates | OTA | Manual |

## Technical Specifications

### Performance

- **Connection Time**: 2-3 seconds (initial)
- **Command Response**: 50-100ms (UDP)
- **Position Update**: Configurable (default 5s)
- **Memory Usage**: ~4KB per motor
- **CPU Usage**: Minimal (async)

### Compatibility

- **Motors**: Somfy Sonesse 30/40 PoE
- **ESP32**: All ESP32 variants
- **ESPHome**: 2023.x and later
- **Home Assistant**: 2023.x and later
- **Network**: WiFi 2.4GHz/5GHz

### Limitations

- **Motors per ESP32**: 1-2 recommended (TLS memory)
- **Network**: Same subnet as motors
- **Configuration**: No motor limit setup
- **Firmware**: No motor firmware updates
- **Certificates**: Self-signed motor certs only

## API Reference

### Available Methods

```cpp
// Motor control
bool move_up()
bool move_down()
bool stop()
bool move_to_position(float position)  // 0-100
bool wink()

// Status queries
float get_position()      // Returns 0-100
const char* get_status()  // Returns "stopped"/"up"/"down"

// Connection management
void reconnect()
```

### YAML Lambda Examples

```yaml
# Open blind
lambda: |-
  auto somfy = (SomfyPoeMotor*)id(somfy_component);
  somfy->move_up();

# Set position
lambda: |-
  auto somfy = (SomfyPoeMotor*)id(somfy_component);
  somfy->move_to_position(50.0);  # 50%

# Get position
lambda: |-
  auto somfy = (SomfyPoeMotor*)id(somfy_component);
  return somfy->get_position();
```

## Configuration Options

### Required Parameters

```yaml
substitutions:
  motor_ip: "192.168.1.150"   # Required
  motor_pin: "1234"            # Required
  motor_name: "Blind"          # Required
```

### Optional Parameters

```yaml
# Update intervals
sensor:
  update_interval: 5s          # Default: 5s (position)

# Logging
logger:
  level: DEBUG                 # DEBUG, INFO, WARN, ERROR

# Network
wifi:
  manual_ip:                   # Optional static IP
    static_ip: 192.168.1.200
    gateway: 192.168.1.1
```

## Supported Commands

### Move Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `move.up` | - | Move to upper limit (open) |
| `move.down` | - | Move to lower limit (close) |
| `move.stop` | - | Stop current movement |
| `move.to` | position (0-100) | Move to specific position |
| `move.wink` | - | Jog motor for identification |

### Status Commands

| Command | Returns | Description |
|---------|---------|-------------|
| `status.position` | position, direction, status | Get current position and state |
| `status.info` | name, model, firmware, etc. | Get motor information |

## Home Assistant Services

### Cover Services

```yaml
# Open cover
service: cover.open_cover
target:
  entity_id: cover.living_room_blind

# Close cover
service: cover.close_cover
target:
  entity_id: cover.living_room_blind

# Stop cover
service: cover.stop_cover
target:
  entity_id: cover.living_room_blind

# Set position
service: cover.set_cover_position
target:
  entity_id: cover.living_room_blind
data:
  position: 50  # 0-100
```

### Button Services

```yaml
# Wink/identify motor
service: button.press
target:
  entity_id: button.living_room_blind_wink

# Reconnect to motor
service: button.press
target:
  entity_id: button.living_room_blind_reconnect
```

## Development Roadmap

### Version 1.0 (Current)

- ✅ Basic motor control
- ✅ Position tracking
- ✅ Home Assistant integration
- ✅ Auto-reconnect

### Version 1.1 (Next)

- 🔲 mDNS discovery
- 🔲 Heartbeat implementation
- 🔲 Enhanced error reporting
- 🔲 Push notifications

### Version 1.2 (Future)

- 🔲 Multiple motor support
- 🔲 Group control
- 🔲 Preset positions
- 🔲 Configuration UI

### Version 2.0 (Long-term)

- 🔲 Advanced motor settings
- 🔲 Lock management
- 🔲 Statistics
- 🔲 Firmware management

## Contributing

Want to help implement features?

1. Check the [planned features](#planned-features) list
2. Open an issue to discuss the feature
3. Fork and implement
4. Submit pull request

Priority areas:
- mDNS discovery implementation
- Multiple motor support
- Push notification handling
- UI improvements

## License

This implementation is provided for educational and interoperability purposes.

Use at your own risk. See [README_ESPHOME.md](README_ESPHOME.md) for details.

---

**Last Updated**: January 2026
**Version**: 1.0
