# Quick Start Guide: ESPHome Somfy PoE Control

Get your Somfy PoE blinds controlled by ESPHome in 10 minutes!

## Prerequisites

- [ ] ESP32 development board
- [ ] USB cable for programming
- [ ] Somfy PoE motor installed and powered
- [ ] Motor IP address and PIN code
- [ ] ESPHome installed ([esphome.io](https://esphome.io/guides/installing_esphome.html))

## Step 1: Find Your Motor Information

### Get Motor IP Address

**Option A: Check your router's DHCP leases**
- Look for devices with hostname `sfy_poe_xxxxxx`

**Option B: Use mDNS discovery**
```bash
# macOS/Linux
dns-sd -B _somfy-poe._tcp local.

# Linux (with avahi)
avahi-browse -t _somfy-poe._tcp
```

**Option C: Ping by hostname**
```bash
# If you know the MAC address (4C:C2:06:16:0D:00)
# Use last 6 hex digits (160d00)
ping sfy_poe_160d00.local
```

### Get Motor PIN Code

- **Located on the motor label** (usually on motor housing)
- **4-digit code** (example: 1234)
- ⚠️ **CRITICAL**: Do not lose this label! PIN cannot be recovered.

## Step 2: Install ESPHome

If you haven't already installed ESPHome:

```bash
# Using pip
pip install esphome

# Or using Home Assistant Add-on
# Go to Supervisor -> Add-on Store -> ESPHome
```

## Step 3: Create Your Project

```bash
# Create project directory
mkdir esphome-somfy
cd esphome-somfy

# Copy the example files
# (Download from repository or copy manually)
```

You need these files:
- `esphome_somfy_poe.yaml` - Main configuration
- `somfy_poe_component.h` - C++ component
- `secrets.yaml` - Your credentials (create from example)

## Step 4: Configure Secrets

Create `secrets.yaml`:

```yaml
wifi_ssid: "YourWiFiNetwork"
wifi_password: "YourWiFiPassword"
api_encryption_key: "generate-with-esphome-wizard"
ota_password: "choose-a-password"
fallback_password: "fallback-password"
```

Generate encryption key:
```bash
esphome wizard temp.yaml
# Copy the generated api_encryption_key to secrets.yaml
# Then delete temp.yaml
```

## Step 5: Update Motor Settings

Edit `esphome_somfy_poe.yaml`:

```yaml
substitutions:
  device_name: somfy-controller
  friendly_name: Somfy PoE Controller

  # UPDATE THESE THREE LINES
  motor_ip: "192.168.1.150"        # Your motor's IP
  motor_pin: "1234"                 # Your motor's PIN
  motor_name: "Living Room Blind"   # Friendly name
```

## Step 6: Connect ESP32

1. Connect ESP32 to computer via USB
2. Note the serial port (usually `/dev/ttyUSB0` on Linux, `COM3` on Windows)

## Step 7: Compile and Upload

```bash
# Validate configuration
esphome config esphome_somfy_poe.yaml

# Compile and upload (first time - via USB)
esphome run esphome_somfy_poe.yaml

# Follow the prompts to select your serial port
```

This will:
1. ✅ Download required libraries
2. ✅ Compile firmware
3. ✅ Upload to ESP32
4. ✅ Show logs in real-time

## Step 8: Test Connection

Watch the logs for:

```
[I][somfy_poe:xxx] Setting up Somfy PoE Motor component
[I][somfy_poe:xxx] Connecting to motor at 192.168.1.150:55056
[I][somfy_poe:xxx] TCP connected, authenticating...
[I][somfy_poe:xxx] Authenticated! Target ID: 4CC206:160D00
[I][somfy_poe:xxx] AES key received
[I][somfy_poe:xxx] Successfully authenticated with motor
```

If you see these messages, **you're connected!** 🎉

## Step 9: Add to Home Assistant

1. Open Home Assistant
2. Go to **Settings** → **Devices & Services**
3. Click **ESPHome** integration
4. Your device should automatically appear
5. Click **Configure** and enter the API encryption key from secrets.yaml

Your blind will appear as:
- **Cover**: `cover.living_room_blind`
- **Sensor**: `sensor.living_room_blind_position`
- **Buttons**: Wink and Reconnect controls

## Step 10: Test Motor Control

In Home Assistant:

1. Open the cover entity
2. Try the controls:
   - **Close** button → blind should close
   - **Open** button → blind should open
   - **Stop** button → stops movement
   - **Position slider** → move to specific position

## Troubleshooting

### "TCP connection failed"

❌ **Problem**: Can't reach motor

✅ **Solutions**:
- Verify IP address: `ping 192.168.1.150`
- Check motor is powered (LED should show activity)
- Ensure ESP32 and motor on same network/subnet
- Check firewall isn't blocking port 55056

### "Authentication failed"

❌ **Problem**: Wrong PIN code

✅ **Solutions**:
- Double-check PIN from motor label
- Ensure no spaces or extra characters
- PIN must be exactly 4 digits
- Try power cycling the motor

### "Not authenticated, cannot send command"

❌ **Problem**: Connection lost

✅ **Solutions**:
- Press "Reconnect" button in Home Assistant
- Check WiFi connection on ESP32
- Restart ESP32
- Check motor LED for errors

### LED Status Guide

Motor LED helps diagnose issues:

| LED Pattern | Meaning | Action |
|-------------|---------|--------|
| Green Blinking | Normal operation | ✅ All good |
| Amber Solid | Limits not set | Run motor setup |
| Red Solid | Obstacle detected | Check for obstruction |
| Red Blinking | Overheated | Wait to cool down |
| Red Fast Blink | No network | Check motor network |
| Off | Idle (normal) | ✅ Ready |

### Still Having Issues?

1. Check logs: `esphome logs esphome_somfy_poe.yaml`
2. Enable verbose logging in YAML: `logger: level: VERBOSE`
3. Verify motor works with official Somfy app
4. Try different ESP32 board
5. Check [README_ESPHOME.md](README_ESPHOME.md) for detailed troubleshooting

## Next Steps

### Multiple Motors

To control more blinds:

**Option 1**: Deploy one ESP32 per motor (recommended)
- More reliable
- Easier to debug
- Just duplicate the configuration with different names

**Option 2**: One ESP32, multiple motors
- See [README_ESPHOME.md](README_ESPHOME.md) for multi-motor setup

### Automation Ideas

**Close at sunset:**
```yaml
automation:
  - alias: "Close blinds at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: cover.close_cover
      target:
        entity_id: cover.living_room_blind
```

**Open in the morning:**
```yaml
automation:
  - alias: "Open blinds at 7 AM weekdays"
    trigger:
      platform: time
      at: "07:00:00"
    condition:
      condition: time
      weekday:
        - mon
        - tue
        - wed
        - thu
        - fri
    action:
      service: cover.open_cover
      target:
        entity_id: cover.living_room_blind
```

**Close when hot:**
```yaml
automation:
  - alias: "Close blinds when hot outside"
    trigger:
      platform: numeric_state
      entity_id: sensor.outdoor_temperature
      above: 85
    action:
      service: cover.close_cover
      target:
        entity_id: cover.living_room_blind
```

## OTA Updates

After initial USB upload, you can update wirelessly:

```bash
# Update over WiFi (much faster!)
esphome run esphome_somfy_poe.yaml
# Select "Over The Air" option
# Or specify IP directly:
esphome run esphome_somfy_poe.yaml --device 192.168.1.200
```

## Getting Help

- **ESPHome Community**: https://community.home-assistant.io/c/esphome/
- **Documentation**: [README_ESPHOME.md](README_ESPHOME.md)
- **Protocol Details**: [SOMFY_POE_API_DOCUMENTATION.md](SOMFY_POE_API_DOCUMENTATION.md)

## Success! 🎉

You now have local control of your Somfy PoE blinds through Home Assistant!

Benefits:
- ✅ **Local Control**: Works without internet
- ✅ **Fast Response**: Direct communication, no cloud delay
- ✅ **Privacy**: All data stays on your network
- ✅ **Automation**: Full Home Assistant integration
- ✅ **Reliable**: No dependency on cloud services

Enjoy your smart blinds! 🏠
