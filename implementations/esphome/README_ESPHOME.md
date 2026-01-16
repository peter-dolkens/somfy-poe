# ESPHome Somfy PoE Motor Control

This is a reference implementation for controlling Somfy PoE motors using ESPHome. It implements the complete Somfy PoE protocol including TLS authentication, PIN verification, and AES-128-CBC encrypted UDP communication.

## Features

- **Full Protocol Implementation**: TCP/TLS authentication + UDP/AES control
- **Home Assistant Integration**: Appears as a native Cover entity
- **Position Tracking**: Real-time blind position monitoring
- **All Motor Commands**: Open, close, stop, position control, wink/identify
- **Automatic Reconnection**: Handles connection drops gracefully
- **mDNS Support**: Can discover motors automatically (optional)

## Hardware Requirements

- **ESP32** board (ESP8266 may work but ESP32 recommended for TLS performance)
- Network connection to same subnet as Somfy PoE motors
- Sufficient power supply (USB 5V 1A minimum)

## Software Requirements

- ESPHome 2023.x or later
- ArduinoJson library (included in ESP32 framework)
- mbedtls library (included in ESP32 framework)

## Installation

### 1. Prepare Configuration Files

Create a directory for your ESPHome project:

```bash
mkdir esphome-somfy
cd esphome-somfy
```

Copy the provided files:
- `esphome_somfy_poe.yaml` - Main ESPHome configuration
- `somfy_poe_component.h` - Custom C++ component

### 2. Create Secrets File

Create `secrets.yaml` with your credentials:

```yaml
# WiFi credentials
wifi_ssid: "YourWiFiSSID"
wifi_password: "YourWiFiPassword"

# ESPHome API encryption key (generate with: esphome wizard)
api_encryption_key: "your-32-char-api-key-here"

# OTA password
ota_password: "your-ota-password"

# Fallback AP password
fallback_password: "fallback-password"
```

### 3. Update Motor Configuration

Edit `esphome_somfy_poe.yaml` and update the substitutions section:

```yaml
substitutions:
  device_name: somfy-controller
  friendly_name: Somfy PoE Controller

  # UPDATE THESE WITH YOUR MOTOR DETAILS
  motor_ip: "192.168.1.150"      # Your motor's IP address
  motor_pin: "1234"               # 4-digit PIN from motor label
  motor_name: "Living Room Blind" # Friendly name for the blind
```

**Finding Your Motor Information:**

1. **IP Address**: Check your router's DHCP leases or use mDNS discovery:
   ```bash
   # macOS/Linux
   dns-sd -B _somfy-poe._tcp local.

   # Or ping by hostname (last 6 digits of MAC address)
   ping sfy_poe_160d00.local
   ```

2. **PIN Code**: Located on the motor label (DO NOT LOSE THIS!)

### 4. Compile and Upload

```bash
# Validate configuration
esphome config esphome_somfy_poe.yaml

# Compile and upload (first time - via USB)
esphome run esphome_somfy_poe.yaml

# Future uploads can be done over-the-air (OTA)
esphome run esphome_somfy_poe.yaml --device 192.168.1.x
```

## Usage

### Home Assistant Integration

Once deployed, the device will automatically appear in Home Assistant:

1. Go to **Settings** → **Devices & Services**
2. Look for **ESPHome** integration
3. Your device should appear as "Somfy PoE Controller"
4. The blind will appear as a Cover entity

### Available Entities

The component creates the following entities:

- **Cover**: `cover.living_room_blind`
  - Open, close, stop controls
  - Position slider (0-100%)
  - Current position display

- **Sensor**: `sensor.living_room_blind_position`
  - Current position percentage

- **Text Sensor**: `sensor.living_room_blind_status`
  - Current status: "stopped", "up", "down"

- **Buttons**:
  - `button.living_room_blind_wink` - Identify motor by jogging
  - `button.living_room_blind_reconnect` - Force reconnection

### Home Assistant Automations

Example automation to close blinds at sunset:

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

Example automation for position control:

```yaml
automation:
  - alias: "Set blinds to 50% when movie starts"
    trigger:
      - platform: state
        entity_id: media_player.living_room_tv
        to: "playing"
    action:
      - service: cover.set_cover_position
        target:
          entity_id: cover.living_room_blind
        data:
          position: 50
```

## Multiple Motors

To control multiple motors, you have two options:

### Option 1: Multiple ESP32 Devices (Recommended)

Deploy one ESP32 per motor or per room. This provides:
- Better reliability (one failure doesn't affect all blinds)
- Distributed processing
- Easier troubleshooting

Simply create multiple configurations with different `device_name` values.

### Option 2: Single ESP32, Multiple Motors

Modify the configuration to create multiple component instances:

```yaml
# In esphome_somfy_poe.yaml, duplicate the custom_component section:

custom_component:
  - lambda: |-
      auto somfy1 = new SomfyPoeMotor("192.168.1.150", "1234");
      App.register_component(somfy1);

      auto somfy2 = new SomfyPoeMotor("192.168.1.151", "5678");
      App.register_component(somfy2);

      return {somfy1, somfy2};

# Then create separate cover entities for each motor
```

## Troubleshooting

### Connection Issues

**Problem**: "TCP connection failed"

**Solutions**:
- Verify motor IP address is correct
- Ensure ESP32 and motor are on same subnet
- Check motor is powered and LED is not showing error
- Ping motor from computer: `ping 192.168.1.150`

**Problem**: "Authentication failed - check PIN code"

**Solutions**:
- Verify PIN code matches label on motor
- PIN must be exactly 4 digits
- Motor may have been factory reset - check if PIN changed

**Problem**: "No authentication response"

**Solutions**:
- Motor may be busy or locked by another controller
- Wait 30 seconds and try reconnecting
- Power cycle the motor
- Check TCP port 55056 is not blocked by firewall

### Motor Not Responding

**Problem**: Commands sent but motor doesn't move

**Solutions**:
- Check motor lock status (may be locked by another controller)
- Verify UDP port 55055 is not blocked
- Check motor LED for error status (see LED status guide below)
- Request position to verify communication: press "Reconnect" button

### LED Status Indicators

Understanding motor LED helps diagnose issues:

- **Green Solid (2s)**: Power up - motor is booting
- **Green Blinking**: Communication active - normal operation
- **Amber Solid**: Limits not set - run limit setup
- **Red Solid**: Obstacle detected - check for obstruction
- **Red Blinking**: Thermal protection - motor overheated
- **Red Fast Blink**: No network/IP - check network connection
- **Off**: Normal idle state

### Debug Logging

Enable verbose logging to diagnose issues:

```yaml
# In esphome_somfy_poe.yaml
logger:
  level: VERBOSE  # Change from DEBUG to VERBOSE
```

Watch logs in real-time:

```bash
esphome logs esphome_somfy_poe.yaml
```

Look for:
- "TCP connected, authenticating..." - connection established
- "Authenticated! Target ID: ..." - authentication successful
- "AES key received" - encryption ready
- "Position: X%, Status: Y" - motor responding

## Advanced Configuration

### Static IP for ESP32

Add to WiFi configuration:

```yaml
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  manual_ip:
    static_ip: 192.168.1.200
    gateway: 192.168.1.1
    subnet: 255.255.255.0
```

### Faster Position Updates

Change update interval (default 5s):

```yaml
sensor:
  - platform: template
    name: "${motor_name} Position"
    update_interval: 2s  # Update every 2 seconds
```

**Note**: Too frequent updates may overwhelm the motor.

### Group Control

To control multiple motors simultaneously, use motor groups configured in the Somfy Config Tool:

```cpp
// Modify send_move_command to use groupID instead of targetID
params["groupID"] = "Living Room";  // Instead of targetID
```

### Intermediate Positions

Motors support 16 preset positions. To use them:

```cpp
// Add to somfy_poe_component.h
bool move_to_preset(uint8_t preset_num) {
  if (preset_num < 1 || preset_num > 16) return false;

  StaticJsonDocument<512> doc;
  doc["id"] = message_id_++;
  doc["method"] = "move.ip";

  JsonObject params = doc.createNestedObject("params");
  params["targetID"] = target_id_;
  params["num"] = preset_num;
  params["seq"] = 1;

  String command;
  serializeJson(doc, command);
  return send_encrypted_udp(command);
}
```

## Security Considerations

### Network Security

- Motors accept connections from any client with correct PIN
- Keep PIN codes secure (4-digit is weak by modern standards)
- Use network segmentation (VLAN) for IoT devices
- Consider firewall rules to limit access to motor ports (55055-55056)

### PIN Protection

- **NEVER commit PIN codes to public repositories**
- Store PINs in `secrets.yaml` (excluded from version control)
- Document PINs in secure password manager
- Motor labels should be kept in safe location

### TLS Certificate Validation

The component uses `setInsecure()` to skip certificate validation because:
- Motors use self-signed certificates
- Validating self-signed certs requires pre-trusting them
- For local network use, risk is minimal

For production deployments, consider:
- Capturing and validating motor certificates
- Using certificate pinning
- See [SOMFY_POE_CERTIFICATES.md](SOMFY_POE_CERTIFICATES.md) for details

## Protocol Details

This implementation follows the official Somfy PoE protocol:

1. **TCP Connection** (Port 55056)
   - TLS/SSL handshake
   - Motor presents self-signed certificate
   - Client optionally presents certificate

2. **PIN Authentication**
   - JSON-RPC request with PIN code
   - Motor responds with Target ID

3. **Key Exchange**
   - Request AES encryption key
   - Motor provides 16-byte key

4. **UDP Commands** (Port 55055)
   - All commands encrypted with AES-128-CBC
   - Random IV for each message
   - PKCS7 padding

For complete protocol documentation, see:
- [SOMFY_POE_API_DOCUMENTATION.md](SOMFY_POE_API_DOCUMENTATION.md)
- [SOMFY_POE_CERTIFICATES.md](SOMFY_POE_CERTIFICATES.md)
- [SOMFY_POE_MDNS_DISCOVERY.md](SOMFY_POE_MDNS_DISCOVERY.md)

## Limitations

### Current Implementation

- **Single Motor Per Instance**: One component controls one motor
- **No Push Notifications**: Position updates are polled, not pushed
- **No Certificate Authentication**: Uses PIN-only mode
- **No Motor Configuration**: Cannot change motor settings (use Config Tool)

### ESPHome/ESP32 Constraints

- **Memory**: ESP32 has limited RAM for TLS connections
- **Concurrent Connections**: Keep to 1-2 motors per ESP32
- **TLS Performance**: Connections may take 2-3 seconds to establish

## Future Enhancements

Potential improvements for community contributions:

- [ ] mDNS auto-discovery integration
- [ ] Support for motor groups
- [ ] Preset position control
- [ ] Configuration entity for PIN change
- [ ] Push notification handling
- [ ] Multi-motor support in single component
- [ ] Speed and ramp configuration
- [ ] Lock state management
- [ ] Heartbeat implementation for connection keep-alive

## Contributing

This is a reference implementation for educational purposes. Feel free to:
- Report issues or improvements
- Submit pull requests
- Fork for your own use
- Share with the community

## References

- **ESPHome Documentation**: https://esphome.io/
- **Somfy PoE Motors**: https://www.somfysystems.com/
- **Driver Analysis**: See `driver_scripts_dec/` directory
- **Protocol Documentation**: See `SOMFY_POE_API_DOCUMENTATION.md`

## License

This implementation is provided for educational and interoperability purposes.

**Disclaimer**: This is an unofficial implementation based on reverse engineering. Somfy®, Sonesse®, and related trademarks are property of Somfy Systems, Inc. Use at your own risk.

## Support

For issues specific to:
- **ESPHome**: https://community.home-assistant.io/c/esphome/
- **Somfy Motors**: (800) 22-SOMFY (76639) | www.somfysystems.com
- **This Implementation**: Check documentation files in this repository

---

**Happy Automating!** 🏠🤖
