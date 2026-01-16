# ESPHome Somfy PoE - Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Home Assistant                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Cover Entity: cover.living_room_blind                   │  │
│  │  - Open / Close / Stop / Set Position                    │  │
│  │  - Current Position: 45%                                 │  │
│  │  - Status: "moving up"                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↕ ESPHome API (Encrypted)            │
└─────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                     ESP32 (SomfyPoeMotor)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Component Logic (somfy_poe_component.h)                 │  │
│  │  - Connection management                                 │  │
│  │  - Authentication state                                  │  │
│  │  - Command queue                                         │  │
│  │  - Position tracking                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                ↓ TCP/TLS (Auth)    ↓ UDP/AES (Commands)         │
└─────────────────────────────────────────────────────────────────┘
                 ↓                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Somfy PoE Motor                             │
│  Port 55056 (TCP/TLS)      Port 55055 (UDP/AES)                 │
│  - Authentication          - Motor commands                      │
│  - Key exchange            - Status queries                      │
│  - Heartbeat              - Position updates                     │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Class Structure

```cpp
class SomfyPoeMotor : public Component {
  // Core ESPHome component that integrates with the framework

  public:
    // Lifecycle methods (ESPHome)
    void setup()    // Called once at boot
    void loop()     // Called repeatedly

    // Motor control methods (exposed to YAML)
    bool move_up()
    bool move_down()
    bool stop()
    bool move_to_position(float position)
    bool wink()

    // Status methods
    float get_position()
    const char* get_status()

  private:
    // Connection & auth
    bool connect_and_authenticate()
    bool authenticate_with_pin()
    bool get_encryption_key()

    // Communication
    bool send_move_command(...)
    bool send_encrypted_udp(...)
    void check_udp_responses()

    // State
    String target_id_          // Motor ID
    uint8_t aes_key_[16]       // Encryption key
    bool is_authenticated_
    float current_position_
}
```

## Communication Flow

### Initial Connection (setup())

```
ESP32 Component                    Somfy Motor
     │                                  │
     ├─────── TCP Connect ──────────────>│ Port 55056
     │        (TLS Handshake)            │
     │<────── TLS Established ───────────┤
     │                                   │
     ├─────── security.auth ────────────>│ PIN: "1234"
     │        {"code": "1234"}           │
     │<────── Authentication OK ─────────┤ targetID
     │        {"targetID": "4CC206..."}  │
     │                                   │
     ├─────── security.get ─────────────>│ Request AES key
     │                                   │
     │<────── AES Key ───────────────────┤ 16-byte key
     │        {"key": [16,247,163...]}   │
     │                                   │
     ├─── TCP Connection Remains ────────┤ Keep-alive
     │                                   │
```

### Motor Control (UDP)

```
ESP32 Component                    Somfy Motor
     │                                  │
     ├── Encrypt with AES ──────────────┐
     │   - Generate random IV            │
     │   - Pad message (PKCS7)           │
     │   - Encrypt with session key      │
     │                                   │
     ├─────── UDP Packet ───────────────>│ Port 55055
     │        [IV(16) + Encrypted Data]  │
     │                                   │
     │<────── UDP Response ───────────────┤
     │        [IV(16) + Encrypted Data]  │
     │                                   │
     ├── Decrypt with AES ──────────────┐
     │   - Extract IV                    │
     │   - Decrypt with session key      │
     │   - Remove padding                │
     │   - Parse JSON                    │
     │                                   │
     └── Update position/status ─────────┘
```

### Position Update Flow

```
Home Assistant          ESP32 Component          Somfy Motor
      │                        │                      │
      ├─── Get Position ──────>│                      │
      │                        ├─── status.position ─>│
      │                        │   (encrypted UDP)    │
      │                        │<──── Position ───────┤
      │                        │   {"position": 45.2} │
      │<─── 45.2% ─────────────┤                      │
      │                        │                      │
```

## Data Flow

### Motor Command Execution

```
1. User Action in Home Assistant
   ↓
2. Home Assistant calls ESPHome API
   cover.set_cover_position(45)
   ↓
3. ESPHome triggers YAML action
   lambda: move_to_position(45.0)
   ↓
4. Component method called
   SomfyPoeMotor::move_to_position(45.0)
   ↓
5. Build JSON command
   {"method": "move.to", "params": {"position": 45}}
   ↓
6. Encrypt with AES-128-CBC
   - Random IV
   - PKCS7 padding
   - AES encryption
   ↓
7. Send UDP packet
   [IV + Encrypted Data] → Motor
   ↓
8. Motor responds
   [IV + Encrypted Response] ← Motor
   ↓
9. Decrypt response
   {"result": true}
   ↓
10. Update internal state
    current_position_ = 45.0
    ↓
11. Home Assistant polls position
    sensor.blind_position → 45%
```

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Home Assistant API                             │
│ - Encrypted with API key                                │
│ - Authentication required                               │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│ Layer 3: ESP32 Network                                  │
│ - WiFi WPA2 encryption                                  │
│ - Local network only                                    │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Motor Control (UDP)                            │
│ - AES-128-CBC encryption                                │
│ - Random IV per message                                 │
│ - Session key from TCP auth                             │
└─────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Motor Authentication (TCP)                     │
│ - TLS/SSL encryption                                    │
│ - 4-digit PIN authentication                            │
│ - Certificate exchange                                  │
└─────────────────────────────────────────────────────────┘
```

## Memory Management

### ESP32 Memory Usage

```
┌─────────────────────────────────────────────────┐
│ ESP32 SRAM (520 KB total)                       │
├─────────────────────────────────────────────────┤
│ ESPHome Core              ~80 KB                │
│ WiFi Stack                ~40 KB                │
│ TLS/SSL (mbedtls)         ~50 KB (per conn)     │
│ ArduinoJson Buffers       ~2 KB                 │
│ AES Encryption Buffers    ~1 KB                 │
│ UDP Buffers               ~2 KB                 │
│ SomfyPoeMotor Component   ~4 KB                 │
│ Other Components          ~20 KB                │
├─────────────────────────────────────────────────┤
│ Available for App         ~321 KB               │
└─────────────────────────────────────────────────┘

💡 Recommendation: Keep to 1-2 motors per ESP32
```

## State Machine

```
┌─────────────┐
│ DISCONNECTED│
└──────┬──────┘
       │ setup() or reconnect()
       ↓
┌─────────────┐
│ CONNECTING  │──────> TCP connection failed ──┐
└──────┬──────┘                                 │
       │ TCP connected                          │
       ↓                                        │
┌─────────────┐                                │
│AUTHENTICATING│──> Auth failed (wrong PIN) ───┤
└──────┬──────┘                                 │
       │ PIN accepted                           │
       ↓                                        │
┌─────────────┐                                │
│ KEY_EXCHANGE│──> Key exchange failed ────────┤
└──────┬──────┘                                 │
       │ AES key received                       │
       ↓                                        │
┌─────────────┐                                │
│ AUTHENTICATED│                                │
│  (Ready)    │                                │
└──────┬──────┘                                 │
       │                                        │
       ├─> send commands (UDP)                  │
       ├─> receive responses (UDP)              │
       ├─> update position                      │
       │                                        │
       └─> Connection lost ────────────────────┘
              (wait 30s, retry)
```

## Performance Considerations

### Timing Characteristics

```
Operation                   Time        Notes
─────────────────────────────────────────────────────────
TCP Connection              1-2s        Includes TLS handshake
PIN Authentication          100-200ms   Single request/response
Key Exchange                100-200ms   Single request/response
UDP Command                 50-100ms    Round-trip time
Motor Movement Start        200-500ms   Physical motor response
Position Update (poll)      50-100ms    UDP query
Total Connection Setup      2-3s        First time only
─────────────────────────────────────────────────────────
```

### Optimization Strategies

1. **Connection Persistence**
   - Keep TCP connection alive for heartbeat
   - Reuse UDP socket
   - Cache AES key in memory

2. **Command Batching**
   - Don't spam commands (motor ignores rapid duplicates)
   - Use sequence numbers to track commands
   - Queue commands if needed

3. **Position Updates**
   - Poll every 5 seconds (default)
   - Increase frequency during movement
   - Cache last known position

## Error Handling

### Connection Errors

```cpp
// Automatic retry logic in loop()
void loop() {
  if (!is_authenticated_ &&
      millis() - last_connect_attempt_ > 30000) {
    // Try reconnecting every 30 seconds
    connect_and_authenticate();
  }
}
```

### UDP Timeout Handling

```cpp
// Check for responses in loop()
void check_udp_responses() {
  int packet_size = udp_.parsePacket();
  if (packet_size > 0) {
    // Process response
  }
  // If no response, command may have been lost
  // Motor will report position on next poll
}
```

### Motor Errors

Motor can report errors in response:

```json
{
  "id": 123,
  "result": false,
  "error": {
    "code": 1,
    "message": "Motor locked"
  }
}
```

Component logs these and continues operation.

## Integration Points

### ESPHome Framework

```cpp
// Register component with ESPHome
App.register_component(somfy);

// Component lifecycle
- constructor()    // Object creation
- setup()          // Initialize (called once)
- loop()           // Main loop (called repeatedly)
- dump_config()    // Log configuration (optional)
```

### YAML Configuration

```yaml
# Lambda expressions bridge YAML to C++
cover:
  - platform: template
    open_action:
      - lambda: |-
          auto somfy = (SomfyPoeMotor*)id(somfy_component);
          somfy->move_up();  # C++ method call
```

### Home Assistant

```
ESPHome Device
  └── Cover Entity (template)
      ├── Attributes
      │   ├── current_position (from sensor)
      │   ├── device_class: blind
      │   └── supported_features: OPEN|CLOSE|STOP|SET_POSITION
      └── Services
          ├── open_cover()
          ├── close_cover()
          ├── stop_cover()
          └── set_cover_position(position)
```

## Testing Strategy

### Unit Testing (Manual)

1. **Connection Test**
   - Verify TCP connection establishes
   - Check authentication succeeds
   - Confirm key exchange

2. **Command Test**
   - Send each command type
   - Verify motor responds
   - Check position updates

3. **Error Recovery**
   - Disconnect network
   - Verify reconnection attempts
   - Test with wrong PIN
   - Power cycle motor

### Integration Testing

1. **Home Assistant**
   - All cover controls work
   - Position slider accurate
   - Status updates correctly

2. **Long-term Stability**
   - Run for 24+ hours
   - Monitor reconnections
   - Check memory leaks

## Future Enhancements

### Planned Features

```
Priority 1 (High Value):
- [ ] mDNS auto-discovery
- [ ] Heartbeat keep-alive
- [ ] Better error reporting to HA

Priority 2 (Nice to Have):
- [ ] Multiple motor support
- [ ] Group control
- [ ] Preset positions
- [ ] Speed configuration

Priority 3 (Advanced):
- [ ] Push notifications from motor
- [ ] Lock state management
- [ ] Configuration via HA UI
- [ ] OTA firmware from motor
```

### Architecture Changes

For multi-motor support:
```cpp
class SomfyPoeController : public Component {
  std::vector<SomfyPoeMotor*> motors_;

  void add_motor(const char* ip, const char* pin);
  void setup_all();
  void loop_all();
}
```

## Debugging

### Enable Verbose Logging

```yaml
logger:
  level: VERBOSE
  logs:
    somfy_poe: VERBOSE
```

### Log Analysis

```
[V][somfy_poe] Sending command: {"method":"move.to",...}
[D][somfy_poe] UDP packet sent: 48 bytes
[D][somfy_poe] UDP response received: 64 bytes
[D][somfy_poe] Decrypted: {"id":123,"result":true}
[D][somfy_poe] Position: 45.0%, Status: moving
```

### Common Debug Points

1. **Connection Issues**: Check TCP handshake logs
2. **Auth Failures**: Verify PIN in logs
3. **Command Issues**: Check UDP send/receive
4. **Encryption Issues**: Verify AES key received

---

## References

- **ESPHome Component Guide**: https://esphome.io/custom/custom_component.html
- **Protocol Documentation**: [../SOMFY_POE_API_DOCUMENTATION.md](../SOMFY_POE_API_DOCUMENTATION.md)
- **mbedtls AES**: https://tls.mbed.org/api/aes_8h.html
- **ArduinoJson**: https://arduinojson.org/

---

**Document Version**: 1.0
**Last Updated**: January 2026
