# Architecture - Somfy PoE Home Assistant Integration

## Overview

This document describes the architecture of the Somfy PoE Home Assistant custom integration.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Home Assistant                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  User Interface (Lovelace)                               │  │
│  │  - Cover controls                                        │  │
│  │  - Config flow UI                                        │  │
│  │  - Automations                                           │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Somfy PoE Integration                                   │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Config Flow (config_flow.py)                      │ │  │
│  │  │  - Discovery (mDNS)                                │ │  │
│  │  │  - Manual setup                                    │ │  │
│  │  │  - Authentication                                  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Coordinator (coordinator.py)                      │ │  │
│  │  │  - Data updates                                    │ │  │
│  │  │  - Connection management                           │ │  │
│  │  │  - Command routing                                 │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Cover Platform (cover.py)                         │ │  │
│  │  │  - Entity implementation                           │ │  │
│  │  │  - State management                                │ │  │
│  │  │  - Services                                        │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Motor Controller (motor.py)                       │ │  │
│  │  │  - TCP/TLS connection                              │ │  │
│  │  │  - UDP/AES encryption                              │ │  │
│  │  │  - Protocol implementation                         │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Discovery (discovery.py)                          │ │  │
│  │  │  - mDNS/Bonjour                                    │ │  │
│  │  │  - Service browsing                                │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               ↕
                  Network (Local LAN)
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                      Somfy PoE Motor                             │
│  Port 55056 (TCP/TLS) | Port 55055 (UDP/AES)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Config Flow (`config_flow.py`)

**Purpose**: Handles user setup through Home Assistant UI

**Features**:
- Automatic motor discovery via mDNS
- Manual IP configuration
- PIN authentication
- Zeroconf integration for background discovery

**Flow**:
```
User Setup → Choose Method (Auto/Manual)
           ↓
Auto:      Discovery → Select Motor → Enter PIN → Create Entry
           ↓
Manual:    Enter IP + PIN → Authenticate → Create Entry
```

### 2. Discovery (`discovery.py`)

**Purpose**: Automatic network discovery of motors

**Technology**: mDNS/Bonjour (Zeroconf)

**Service Type**: `_somfy-poe._tcp.local.`

**TXT Record Data**:
- `targetid`: Motor unique ID
- `model`: Motor model name
- `mac`: MAC address
- `firmware`: Firmware version
- `name`: User-assigned name

**Classes**:
- `SomfyPoEMotor`: Discovered motor info
- `SomfyPoEDiscovery`: Service listener
- `async_discover_motors()`: Discovery function

### 3. Motor Controller (`motor.py`)

**Purpose**: Low-level protocol implementation

**Responsibilities**:
- TCP/TLS connection management
- PIN authentication
- AES key exchange
- UDP command encryption/decryption
- Motor control commands

**Key Methods**:
- `connect()`: Full connection sequence
- `move_up/down/stop()`: Movement commands
- `move_to_position()`: Position control
- `get_position()`: Status query
- `get_info()`: Motor information

**Security**:
- TLS for authentication channel
- AES-128-CBC for command channel
- Random IV per message
- PKCS7 padding

### 4. Coordinator (`coordinator.py`)

**Purpose**: Data update and command coordination

**Type**: `DataUpdateCoordinator`

**Features**:
- Periodic position updates (5 seconds)
- Automatic reconnection
- Command forwarding
- State caching

**Update Cycle**:
```
Update Timer → Check Connection → Get Position → Update State
                     ↓
             Reconnect if needed
```

### 5. Cover Platform (`cover.py`)

**Purpose**: Home Assistant cover entity

**Entity Type**: `CoverEntity`

**Device Class**: `BLIND`

**Supported Features**:
- `OPEN`: Move to upper limit
- `CLOSE`: Move to lower limit
- `STOP`: Stop movement
- `SET_POSITION`: Position control (0-100)

**State Mapping**:
```
Somfy Protocol:  0 = Open, 100 = Closed
Home Assistant:  0 = Closed, 100 = Open
(Inverted in implementation)
```

**Attributes**:
- Position (0-100%)
- Direction (up/down/stopped)
- Status (ok/obstacle/thermal)
- Target ID
- Firmware version
- Model

## Data Flow

### Setup Flow

```
1. User initiates setup
   ↓
2. Config Flow starts
   ↓
3. Discovery scans network (if auto)
   ↓
4. User selects motor and enters PIN
   ↓
5. Config entry created
   ↓
6. Integration loads
   ↓
7. Coordinator initializes
   ↓
8. Motor controller connects
   ↓
9. Cover entity created
   ↓
10. Device appears in Home Assistant
```

### Command Flow

```
User Action (UI)
  ↓
Cover Entity (cover.py)
  ↓
Coordinator (coordinator.py)
  ↓
Motor Controller (motor.py)
  ↓
[Encrypt with AES]
  ↓
UDP Packet → Motor
  ↓
[Response received]
  ↓
[Decrypt with AES]
  ↓
Coordinator updates state
  ↓
UI reflects new state
```

### Update Flow

```
Timer triggers (every 5 seconds)
  ↓
Coordinator requests update
  ↓
Motor Controller sends status.position
  ↓
Motor responds with current state
  ↓
Coordinator processes response
  ↓
Cover entity state updated
  ↓
UI shows current position
```

## Communication Protocol

### Initial Authentication (TCP/TLS)

```python
# Port 55056, TLS encrypted
1. TCP Connect + TLS Handshake
2. security.auth {"code": "1234"}
   ← {"targetID": "4CC206:160D00"}
3. security.get
   ← {"key": [16 bytes]}
```

### Motor Commands (UDP/AES)

```python
# Port 55055, AES-128-CBC encrypted
[IV (16 bytes) + Encrypted JSON]

Plaintext JSON:
{
  "id": 123,
  "method": "move.to",
  "params": {
    "targetID": "4CC206:160D00",
    "position": 50.0,
    "seq": 1
  }
}

Response:
{
  "id": 123,
  "result": true
}
```

## State Management

### Entity States

- **State**: `open`, `closed`, `opening`, `closing`
- **Position**: 0-100 (0=closed, 100=open)
- **Available**: Connection status

### Attributes

Stored in `extra_state_attributes`:
- Direction
- Status
- Target ID
- Firmware
- Model
- MAC

### Persistence

- Config stored in `.storage/core.config_entries`
- Entity states in `.storage/core.entity_registry`
- No local caching of position (always from motor)

## Error Handling

### Connection Errors

```python
try:
    await motor.connect()
except ConnectionError:
    # Mark unavailable
    # Schedule reconnect
```

### Command Errors

```python
try:
    await motor.move_to_position(50)
except Exception:
    # Log error
    # Don't update state
```

### Reconnection

```python
if not motor.is_connected:
    await motor.disconnect()
    await motor.connect()
```

## Performance Considerations

### Update Frequency

- Default: 5 seconds
- Configurable in options
- Increased during movement (future enhancement)

### Connection Persistence

- Single TCP connection kept alive
- UDP socket reused
- AES key cached in memory

### Resource Usage

Per motor:
- Memory: ~1 MB
- CPU: Minimal (async I/O)
- Network: ~1 KB/sec

## Security

### Authentication

1. TLS for TCP channel (self-signed cert accepted)
2. PIN-based authentication
3. AES key exchange over TLS

### Encryption

- Command encryption: AES-128-CBC
- Random IV per message
- PKCS7 padding
- Session key per connection

### Network

- Local network only
- No cloud communication
- No credentials stored in plaintext

## Extensibility

### Adding New Features

1. **New commands**: Add to `motor.py`
2. **New services**: Register in `cover.py`
3. **New options**: Add to config flow
4. **New attributes**: Add to cover entity

### Configuration Options

Current:
- Update interval

Future:
- Poll during movement
- Push notifications
- Custom timeout values

## File Structure

```
custom_components/somfy_poe/
├── __init__.py           # Integration setup
├── manifest.json         # Integration metadata
├── const.py             # Constants
├── config_flow.py       # UI configuration
├── coordinator.py       # Data coordinator
├── cover.py            # Cover platform
├── motor.py            # Protocol implementation
├── discovery.py        # mDNS discovery
├── strings.json        # UI strings
└── services.yaml       # Service definitions
```

## Dependencies

### Required

- `zeroconf>=0.131.0` - mDNS discovery
- `pycryptodome>=3.19.0` - AES encryption

### Home Assistant

- Minimum version: 2023.1.0
- Config flow support
- DataUpdateCoordinator
- Cover platform

## Testing

### Test Levels

1. **Unit Tests**: Individual functions (future)
2. **Integration Tests**: Full flow (manual)
3. **Hardware Tests**: Real motors (required)

### Test Script

`test_connection.py` provides:
- Discovery test
- Connection test
- Command test
- Information retrieval

## Future Enhancements

### Planned Features

- [ ] Multiple motors per entry
- [ ] Group command support
- [ ] Position presets (favorites)
- [ ] Push notifications from motor
- [ ] Diagnostics data
- [ ] Improved reconnection logic
- [ ] Scene support
- [ ] Increased poll rate during movement

### Architecture Changes

For multiple motors:
```python
class SomfyPoEHub:
    motors: Dict[str, SomfyPoEMotorController]

    async def add_motor(self, config):
        motor = SomfyPoEMotorController(...)
        self.motors[target_id] = motor
```

## Troubleshooting Architecture

### Debug Flow

```
1. Enable debug logging
   ↓
2. Reproduce issue
   ↓
3. Check logs for component
   ↓
4. Identify failure point:
   - Discovery?
   - Connection?
   - Authentication?
   - Command execution?
   - State update?
   ↓
5. Apply fix
```

### Common Issues

| Issue | Component | Solution |
|-------|-----------|----------|
| Discovery fails | `discovery.py` | Check mDNS |
| Auth fails | `motor.py` | Check PIN |
| No response | `motor.py` | Check network |
| Wrong position | `cover.py` | Check inversion |

## References

- [Home Assistant Integration Guide](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [DataUpdateCoordinator](https://developers.home-assistant.io/docs/integration_fetching_data)
- [Cover Platform](https://developers.home-assistant.io/docs/core/entity/cover)

---

**Document Version**: 1.0
**Last Updated**: January 2026
