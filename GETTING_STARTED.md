# Getting Started with Somfy PoE Motor Control

Welcome! This repository contains everything you need to control Somfy PoE motors using open-source home automation platforms.

## What's Available

### 📚 Complete Protocol Documentation

Reverse-engineered documentation of the Somfy PoE motor protocol:

- **[SOMFY_POE_API_DOCUMENTATION.md](SOMFY_POE_API_DOCUMENTATION.md)** - Complete API reference with examples in Python and JavaScript
- **[SOMFY_POE_CERTIFICATES.md](SOMFY_POE_CERTIFICATES.md)** - TLS/SSL certificate guide
- **[SOMFY_POE_MDNS_DISCOVERY.md](SOMFY_POE_MDNS_DISCOVERY.md)** - Network discovery guide
- **[DRIVER_FORMAT.md](DRIVER_FORMAT.md)** - Analysis of official driver

### 🔧 Reference Implementations

Ready-to-use implementations for popular platforms:

- **[ESPHome Implementation](implementations/esphome/)** - Control motors with ESP32 and Home Assistant

## Quick Start Options

### Option 1: ESPHome + Home Assistant (Recommended) ⭐

**Best for**: Home Assistant users who want local control

**What you need**:
- ESP32 board (~$5-10)
- Somfy PoE motor with IP and PIN
- Home Assistant installation

**Time to setup**: ~10 minutes

**[👉 Start here: ESPHome Quick Start](implementations/esphome/QUICKSTART_ESPHOME.md)**

### Option 2: Custom Python Implementation

**Best for**: Python developers who want to integrate into custom systems

**What you need**:
- Python 3.7+
- Network access to motors
- Motor IP and PIN

**Time to setup**: ~30 minutes

**[👉 Start here: Python API Documentation](SOMFY_POE_API_DOCUMENTATION.md#python-example-complete-control-session)**

### Option 3: Custom Node.js Implementation

**Best for**: JavaScript/Node.js developers

**What you need**:
- Node.js 14+
- Network access to motors
- Motor IP and PIN

**Time to setup**: ~30 minutes

**[👉 Start here: Node.js API Documentation](SOMFY_POE_API_DOCUMENTATION.md#javascriptnodejs-example)**

## Understanding the System

### How Somfy PoE Motors Work

```
┌─────────────────────────────────────────────────────────┐
│                  Your Home Network                       │
│                                                          │
│  ┌──────────┐           ┌──────────┐                   │
│  │ Controller│◄─────────►│ PoE Motor│                   │
│  │ (ESP32/PC)│  Local    │ (Blind)   │                   │
│  └──────────┘  Control   └──────────┘                   │
│                                                          │
│  • No internet required                                 │
│  • No cloud service                                     │
│  • Direct local communication                           │
└─────────────────────────────────────────────────────────┘
```

### Communication Protocol

1. **TCP Connection (Port 55056)**
   - TLS/SSL encrypted
   - Used for authentication
   - PIN-based login

2. **UDP Commands (Port 55055)**
   - AES-128-CBC encrypted
   - Used for all motor control
   - Fast, lightweight

3. **mDNS Discovery**
   - Automatic motor detection
   - No manual IP configuration needed

## Before You Start

### Required Information

You'll need these details for your motor:

1. **IP Address**: Find it in your router's DHCP leases
   - Hostname format: `sfy_poe_xxxxxx.local`
   - Or use the discovery tools

2. **PIN Code**: 4-digit code on motor label
   - ⚠️ **CRITICAL**: Do not lose the motor label!
   - PIN cannot be recovered if lost

3. **Motor Name**: Choose a friendly name
   - Example: "Living Room Blind"

### Network Requirements

- Motor and controller on **same subnet**
- Firewall allows:
  - **TCP port 55056** (authentication)
  - **UDP port 55055** (commands)
  - **UDP port 5353** (mDNS discovery, optional)

## Repository Structure

```
somfy/
├── GETTING_STARTED.md (this file)
│
├── Protocol Documentation
│   ├── SOMFY_POE_API_DOCUMENTATION.md    # Complete API reference
│   ├── SOMFY_POE_CERTIFICATES.md         # Certificate guide
│   ├── SOMFY_POE_MDNS_DISCOVERY.md       # Discovery guide
│   └── DRIVER_FORMAT.md                  # Driver analysis
│
├── Reference Materials
│   ├── references/                        # Official Somfy documentation
│
└── Implementations
    └── esphome/                           # ESPHome implementation
        ├── QUICKSTART_ESPHOME.md         # Quick start guide
        ├── README_ESPHOME.md             # Full documentation
        ├── ARCHITECTURE.md               # Architecture details
        ├── FEATURES.md                   # Feature list
        ├── esphome_somfy_poe.yaml        # Configuration
        ├── somfy_poe_component.h         # C++ component
        └── secrets.yaml.example          # Secrets template
```

## Common Use Cases

### Home Automation

Integrate blinds with your smart home:

```yaml
# Example: Close blinds at sunset
automation:
  - alias: "Close at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: cover.close_cover
      entity_id: cover.living_room_blind
```

### Voice Control

Control blinds with Alexa/Google Assistant via Home Assistant:

```
"Alexa, open the living room blinds"
"Hey Google, set bedroom blinds to 50%"
```

### Scheduling

Create daily schedules:

```yaml
# Open blinds weekday mornings
automation:
  - alias: "Morning blinds"
    trigger:
      platform: time
      at: "07:00:00"
    condition:
      condition: time
      weekday: [mon, tue, wed, thu, fri]
    action:
      service: cover.open_cover
      entity_id: cover.bedroom_blind
```

### Temperature Control

Integrate with temperature sensors:

```yaml
# Close when hot outside
automation:
  - alias: "Close on hot days"
    trigger:
      platform: numeric_state
      entity_id: sensor.outdoor_temperature
      above: 85
    action:
      service: cover.close_cover
      entity_id: cover.south_facing_blinds
```

## Troubleshooting

### Can't find motor IP address?

```bash
# Use mDNS discovery
dns-sd -B _somfy-poe._tcp local.

# Or scan your network
nmap -sn 192.168.1.0/24 | grep -i somfy
```

### Connection fails?

1. Verify motor is powered (check LED)
2. Ping the motor: `ping 192.168.1.150`
3. Check firewall allows ports 55055-55056
4. Ensure same subnet

### Authentication fails?

1. Double-check PIN from motor label
2. Ensure PIN is exactly 4 digits
3. Try factory reset (see motor manual)

### Motor doesn't respond?

1. Check motor LED status (see LED guide in docs)
2. Verify motor isn't locked by another controller
3. Test with official Somfy app
4. Power cycle motor

## Support & Community

### Documentation

- **[API Reference](SOMFY_POE_API_DOCUMENTATION.md)** - Complete protocol details
- **[ESPHome Guide](implementations/esphome/README_ESPHOME.md)** - ESPHome documentation
- **[Architecture](implementations/esphome/ARCHITECTURE.md)** - System architecture

### Getting Help

- **ESPHome Issues**: [ESPHome Community](https://community.home-assistant.io/c/esphome/)
- **Protocol Questions**: Open an issue in this repository
- **Somfy Support**: (800) 22-SOMFY (76639) | www.somfysystems.com

### Contributing

Contributions welcome!

- Report bugs or issues
- Submit documentation improvements
- Create new platform implementations
- Share automation examples

See [implementations/README.md](implementations/README.md) for contribution guidelines.

## Security & Privacy

### Local Control

- ✅ **No cloud required**: Direct local communication
- ✅ **No data collection**: Nothing leaves your network
- ✅ **Works offline**: Internet not required
- ✅ **Fast**: No cloud latency

### Security Layers

1. **Network**: WiFi WPA2 encryption
2. **Authentication**: PIN-based motor access
3. **Transport**: TLS/SSL for TCP connection
4. **Commands**: AES-128 encryption for UDP

### Best Practices

- Keep PIN codes secure
- Use strong WiFi password
- Segment IoT devices on separate VLAN
- Regular firmware updates for controllers
- Document motor locations and PINs securely

## What You Can Do

With this implementation, you can:

- ✅ Open/close blinds remotely
- ✅ Set specific positions (0-100%)
- ✅ Create automations based on time, sun, temperature
- ✅ Voice control via Alexa/Google Assistant
- ✅ Control from anywhere with VPN/Nabu Casa
- ✅ Group control (multiple blinds)
- ✅ Status monitoring
- ✅ Integration with other smart devices

## What You Cannot Do

Current limitations:

- ❌ Cannot set motor limits (use Somfy Config Tool)
- ❌ Cannot update motor firmware
- ❌ Cannot configure motor network settings initially
- ❌ Cannot change motor PIN

For these tasks, use the official Somfy PoE Config Tool.

## Next Steps

1. **Choose your platform**:
   - [ESPHome](implementations/esphome/QUICKSTART_ESPHOME.md) for Home Assistant
   - [Python API](SOMFY_POE_API_DOCUMENTATION.md#python-example-complete-control-session) for custom integration
   - [Node.js API](SOMFY_POE_API_DOCUMENTATION.md#javascriptnodejs-example) for JavaScript projects

2. **Gather motor information**:
   - Find IP address
   - Locate PIN code
   - Test connectivity

3. **Follow quick start guide**:
   - Install required software
   - Configure settings
   - Test connection
   - Control your blinds!

## Success Stories

Once set up, you can:

> "My blinds now automatically open at sunrise and close at sunset. No more manually adjusting them every day!"

> "Integrated with my temperature sensors - blinds close automatically on hot days to keep the house cool."

> "Voice control is awesome - I can tell Alexa to close all blinds when watching movies."

> "Best part? Everything works locally. No cloud dependencies or subscriptions!"

## Support This Project

If you find this useful:

- ⭐ Star the repository
- 📢 Share with others
- 🐛 Report issues
- 🔧 Contribute improvements
- 📖 Improve documentation
- 💡 Share your automations

## Legal Notice

This is an **unofficial**, **reverse-engineered** implementation for educational and interoperability purposes.

- **Somfy®**, **Sonesse®** are trademarks of Somfy Systems, Inc.
- Not endorsed or supported by Somfy
- Use at your own risk
- May void warranties

## Acknowledgments

- Reverse engineering based on driver analysis
- Community testing and feedback
- ESPHome and Home Assistant projects
- Open-source encryption libraries

---

## Ready to Start?

**[👉 ESPHome Quick Start (Recommended)](implementations/esphome/QUICKSTART_ESPHOME.md)**

**[👉 View All Documentation](README.md)**

**[👉 Browse Implementations](implementations/)**

---

**Questions?** Open an issue or check the documentation!

**Happy Automating!** 🏠🤖
