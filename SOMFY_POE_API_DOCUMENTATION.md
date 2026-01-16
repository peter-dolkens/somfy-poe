# Somfy PoE Motor API Documentation

## Overview

This documentation describes the local control API for Somfy Power over Ethernet (PoE) motors. The API allows for direct, local network control of Somfy Sonesse 30 and Sonesse 40 PoE motors without requiring cloud connectivity.

**Document Version:** 1.0
**Last Updated:** January 2026
**Based on:** Somfy PoE Motor Driver v1.2.1 (October 2024)

---

## Table of Contents

1. [Connection & Security](#connection--security)
2. [Communication Protocols](#communication-protocols)
3. [Authentication Flow](#authentication-flow)
4. [API Methods](#api-methods)
5. [Message Format](#message-format)
6. [Motor Control](#motor-control)
7. [Status & Configuration](#status--configuration)
8. [Group Control](#group-control)
9. [Code Examples](#code-examples)

---

## Connection & Security

### Network Requirements

- **Protocol:** HTTPS over TCP (Port 55056) for authentication, UDP (Port 55055) for commands
- **IP Assignment:** DHCP (default) or Static IP
- **PoE Standard:** IEEE 802.3at (PoE+) Type 2 (30W) minimum
- **Cable:** CAT-5e SF/UTP (Shielded & Foiled) or higher recommended
- **Discovery:** mDNS/Bonjour for hostname resolution

### Security

The Somfy PoE API uses multi-layer security:

1. **TLS/SSL:** Certificate-based mutual authentication
2. **PIN Authentication:** 4-digit PIN code (printed on motor label)
3. **AES-128 Encryption:** All UDP communications encrypted with session key

#### Certificate Requirements

- Client must present valid TLS certificate
- Motor presents self-signed certificate
- Certificate verification can be configured (see SSL status codes)

---

## Communication Protocols

### TCP (HTTPS - Port 55056)

Used for:
- Initial authentication
- Authorization and key exchange
- Heartbeat messages

### UDP (Port 55055)

Used for:
- Motor discovery (broadcast)
- All motor control commands
- Status queries
- Push notifications

**Important:** UDP messages MUST be encrypted using AES-128-CBC with the session key obtained during authorization.

---

## Authentication Flow

### Step 1: TCP Connection & SSL Handshake

```
Client → Motor (TCP 55056)
  - Establish TLS connection
  - Present client certificate
  - Motor presents certificate
```

### Step 2: Authentication (PIN)

**Request:**
```json
{
  "id": 12345,
  "method": "security.auth",
  "params": {
    "code": "1234"
  }
}
```

**Response:**
```json
{
  "id": 12345,
  "targetID": "4CC206:160D00",
  "result": true
}
```

The `targetID` is the unique identifier for this motor (MAC-based).

### Step 3: Authorization (Key Exchange)

**Request:**
```json
{
  "id": 12346,
  "method": "security.get"
}
```

**Response:**
```json
{
  "id": 12346,
  "result": true,
  "key": [16, 247, 163, 238, ...]  // 16-byte AES key as byte array
}
```

### Step 4: Discovery (Optional)

Broadcast a ping to discover all motors on the network:

**Request (UDP broadcast to 255.255.255.255:55055, encrypted):**
```json
{
  "id": 12347,
  "method": "status.ping",
  "params": {
    "targetID": "*"
  }
}
```

Each motor responds with its `targetID`.

---

## API Methods

### Motor Control Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `move.up` | Move to upper limit | targetID, seq |
| `move.down` | Move to lower limit | targetID, seq |
| `move.stop` | Stop movement | targetID, seq |
| `move.to` | Move to position (0-100%) | targetID, position, seq |
| `move.ip` | Move to intermediate position | targetID, num (1-16), seq |
| `move.ip.nextup` | Move to next IP up | targetID, seq |
| `move.ip.nextdown` | Move to next IP down | targetID, seq |
| `move.relative` | Move relative (timed) | targetID, duration (ms), direction, seq |
| `move.wink` | Jog motor (identify) | targetID, seq |

### Status Query Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `status.ping` | Ping motor/discover | targetID |
| `status.info` | Get motor information | name, model, firmware, hardware, mac, hostname |
| `status.position` | Get current position | position, direction, status |
| `status.ipv4` | Get network config | dhcp, ipaddress, subnetmask, gateway, dns1, dns2 |
| `status.speed` | Get speed settings | up, down |
| `status.speeds.range` | Get speed range | min, max |
| `status.ramps` | Get ramp settings | softstart up/down, softstop up/down |
| `status.ramps.range` | Get ramp range | min, max |
| `status.led` | Get LED status | enabled |
| `status.ip` | Get intermediate positions | Array of 16 positions |

### Lock Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `lock.get` | Get lock state | targetID |
| `lock.set` | Set lock state | targetID, state (boolean), priority |

### Group Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `group.get` | Get group memberships | targetID → returns group array |
| `move.*` (with groupID) | Any move command | groupID instead of targetID |

---

## Message Format

### Command Message Structure

All commands follow this JSON-RPC inspired format:

```json
{
  "id": <unique_integer>,
  "method": "<method_name>",
  "params": {
    "targetID": "<motor_id>",
    // method-specific parameters
  }
}
```

### Response Message Structure

```json
{
  "id": <matching_request_id>,
  "targetID": "<motor_id>",
  "result": true|false,
  "method": "<method_name>",  // optional, for push notifications
  "params": {
    // method-specific response data
  },
  // method-specific top-level fields
  "position": { ... },
  "info": { ... },
  "ipv4": { ... },
  "group": [ ... ],
  "lock": true|false
}
```

### Error Response

```json
{
  "id": <request_id>,
  "result": false,
  "error": {
    "code": <error_code>,
    "message": "<error_description>"
  }
}
```

---

## Motor Control

### Move to Upper Limit

**Request:**
```json
{
  "id": 100,
  "method": "move.up",
  "params": {
    "targetID": "4CC206:160D00",
    "seq": 1
  }
}
```

**Response:**
```json
{
  "id": 100,
  "targetID": "4CC206:160D00",
  "result": true
}
```

### Move to Position (0-100%)

**Request:**
```json
{
  "id": 101,
  "method": "move.to",
  "params": {
    "targetID": "4CC206:160D00",
    "position": 75.5,
    "seq": 1
  }
}
```

**Response:**
```json
{
  "id": 101,
  "targetID": "4CC206:160D00",
  "result": true
}
```

**Position Encoding:**
- `0` = Fully open (upper limit)
- `100` = Fully closed (lower limit)
- Position values are floating point (e.g., 75.5)

### Move to Intermediate Position

Motors support 16 preset intermediate positions (1-16).

**Request:**
```json
{
  "id": 102,
  "method": "move.ip",
  "params": {
    "targetID": "4CC206:160D00",
    "num": 3,
    "seq": 1
  }
}
```

### Move Relative (Timed Movement)

Move for a specific duration in milliseconds.

**Request:**
```json
{
  "id": 103,
  "method": "move.relative",
  "params": {
    "targetID": "4CC206:160D00",
    "duration": 5000,
    "direction": "up",
    "seq": 1
  }
}
```

**Parameters:**
- `duration`: Milliseconds (max 60000)
- `direction`: "up" or "down"

### Stop Movement

**Request:**
```json
{
  "id": 104,
  "method": "move.stop",
  "params": {
    "targetID": "4CC206:160D00",
    "seq": 1
  }
}
```

### Wink/Identify Motor

Makes the motor jog briefly to identify which physical motor is being controlled.

**Request:**
```json
{
  "id": 105,
  "method": "move.wink",
  "params": {
    "targetID": "4CC206:160D00",
    "seq": 1
  }
}
```

---

## Status & Configuration

### Get Motor Information

**Request:**
```json
{
  "id": 200,
  "method": "status.info",
  "params": {
    "targetID": "4CC206:160D00"
  }
}
```

**Response:**
```json
{
  "id": 200,
  "targetID": "4CC206:160D00",
  "result": true,
  "info": {
    "name": "Living Room Shade",
    "model": "Sonesse 30 PoE",
    "firmware": "1.2.0",
    "hardware": "1.0",
    "mac": "4C:C2:06:16:0D:00",
    "hostname": "sfy_poe_000246"
  }
}
```

### Get Current Position

**Request:**
```json
{
  "id": 201,
  "method": "status.position",
  "params": {
    "targetID": "4CC206:160D00"
  }
}
```

**Response:**
```json
{
  "id": 201,
  "targetID": "4CC206:160D00",
  "result": true,
  "position": {
    "value": 45.2,
    "direction": "stopped",
    "status": "ok"
  }
}
```

**Direction values:**
- `"stopped"` - Motor is idle
- `"up"` - Moving toward upper limit
- `"down"` - Moving toward lower limit

**Status values:**
- `"ok"` - Normal operation
- `"obstacle"` - Obstacle detected
- `"thermal"` - Thermal protection activated

### Get Network Configuration

**Request:**
```json
{
  "id": 202,
  "method": "status.ipv4",
  "params": {
    "targetID": "4CC206:160D00"
  }
}
```

**Response:**
```json
{
  "id": 202,
  "targetID": "4CC206:160D00",
  "result": true,
  "ipv4": {
    "dhcp": true,
    "ipaddress": "192.168.1.150",
    "subnetmask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns1": "192.168.1.1",
    "dns2": "0.0.0.0"
  }
}
```

### Get Lock State

**Request:**
```json
{
  "id": 203,
  "method": "lock.get",
  "params": {
    "targetID": "4CC206:160D00"
  }
}
```

**Response:**
```json
{
  "id": 203,
  "targetID": "4CC206:160D00",
  "result": true,
  "lock": false
}
```

### Set Lock State

When locked, the motor will not respond to movement commands (except from priority sources).

**Request:**
```json
{
  "id": 204,
  "method": "lock.set",
  "params": {
    "targetID": "4CC206:160D00",
    "state": true,
    "priority": 1
  }
}
```

**Priority values:**
- `1` - Lock enabled
- `2` - Lock disabled

---

## Group Control

Motors can be organized into named groups for simultaneous control.

### Get Group Memberships

**Request:**
```json
{
  "id": 300,
  "method": "group.get",
  "params": {
    "targetID": "4CC206:160D00"
  }
}
```

**Response:**
```json
{
  "id": 300,
  "targetID": "4CC206:160D00",
  "result": true,
  "group": [
    "Living Room",
    "All Shades",
    "South Facing"
  ]
}
```

### Control a Group

Replace `targetID` with `groupID` in the params:

**Request:**
```json
{
  "id": 301,
  "method": "move.to",
  "params": {
    "groupID": "Living Room",
    "position": 50,
    "seq": 1
  }
}
```

All motors in the "Living Room" group will move to 50% position simultaneously.

---

## Code Examples

### Python Example: Complete Control Session

```python
import socket
import ssl
import json
import struct
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class SomfyPoEController:
    def __init__(self, motor_ip, pin_code):
        self.motor_ip = motor_ip
        self.pin_code = pin_code
        self.tcp_port = 55056
        self.udp_port = 55055
        self.target_id = None
        self.aes_key = None
        self.tcp_socket = None
        self.udp_socket = None
        self.message_id = 1

    def connect(self):
        """Establish TCP connection with TLS"""
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Load client certificate if you have one
        # context.load_cert_chain('client_cert.pem', 'client_key.pem')

        # Create and wrap socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket = context.wrap_socket(sock, server_hostname=self.motor_ip)
        self.tcp_socket.connect((self.motor_ip, self.tcp_port))

        print(f"Connected to {self.motor_ip}:{self.tcp_port}")

    def send_tcp(self, message):
        """Send JSON message over TCP"""
        data = json.dumps(message)
        self.tcp_socket.sendall(data.encode('utf-8'))
        response = self.tcp_socket.recv(4096).decode('utf-8')
        return json.loads(response)

    def authenticate(self):
        """Authenticate with PIN code"""
        message = {
            "id": self.message_id,
            "method": "security.auth",
            "params": {
                "code": self.pin_code
            }
        }
        self.message_id += 1

        response = self.send_tcp(message)

        if response.get('result'):
            self.target_id = response.get('targetID')
            print(f"Authenticated! Target ID: {self.target_id}")
            return True
        else:
            print("Authentication failed!")
            return False

    def authorize(self):
        """Get AES encryption key"""
        message = {
            "id": self.message_id,
            "method": "security.get"
        }
        self.message_id += 1

        response = self.send_tcp(message)

        if response.get('result'):
            key_bytes = response.get('key', [])
            self.aes_key = bytes(key_bytes)
            print(f"Authorization successful! Key length: {len(self.aes_key)}")

            # Setup UDP socket
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return True
        else:
            print("Authorization failed!")
            return False

    def encrypt_message(self, message):
        """Encrypt message with AES-128-CBC"""
        # Generate random IV
        iv = get_random_bytes(16)

        # Create cipher
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)

        # Pad message to multiple of 16 bytes
        message_bytes = message.encode('utf-8')
        padding_length = 16 - (len(message_bytes) % 16)
        padded_message = message_bytes + (bytes([padding_length]) * padding_length)

        # Encrypt
        encrypted = cipher.encrypt(padded_message)

        # Return IV + encrypted data
        return iv + encrypted

    def decrypt_message(self, data):
        """Decrypt AES-128-CBC message"""
        # Extract IV and encrypted data
        iv = data[:16]
        encrypted = data[16:]

        # Create cipher
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)

        # Decrypt
        decrypted = cipher.decrypt(encrypted)

        # Remove padding
        padding_length = decrypted[-1]
        message = decrypted[:-padding_length]

        return message.decode('utf-8')

    def send_udp(self, message):
        """Send encrypted UDP message"""
        data = json.dumps(message)
        encrypted = self.encrypt_message(data)

        self.udp_socket.sendto(encrypted, (self.motor_ip, self.udp_port))

        # Receive response
        response_data, _ = self.udp_socket.recvfrom(4096)
        decrypted = self.decrypt_message(response_data)
        return json.loads(decrypted)

    def move_to_position(self, position):
        """Move motor to position (0-100)"""
        message = {
            "id": self.message_id,
            "method": "move.to",
            "params": {
                "targetID": self.target_id,
                "position": position,
                "seq": 1
            }
        }
        self.message_id += 1

        response = self.send_udp(message)
        return response.get('result', False)

    def move_up(self):
        """Move to upper limit"""
        message = {
            "id": self.message_id,
            "method": "move.up",
            "params": {
                "targetID": self.target_id,
                "seq": 1
            }
        }
        self.message_id += 1

        response = self.send_udp(message)
        return response.get('result', False)

    def move_down(self):
        """Move to lower limit"""
        message = {
            "id": self.message_id,
            "method": "move.down",
            "params": {
                "targetID": self.target_id,
                "seq": 1
            }
        }
        self.message_id += 1

        response = self.send_udp(message)
        return response.get('result', False)

    def stop(self):
        """Stop movement"""
        message = {
            "id": self.message_id,
            "method": "move.stop",
            "params": {
                "targetID": self.target_id,
                "seq": 1
            }
        }
        self.message_id += 1

        response = self.send_udp(message)
        return response.get('result', False)

    def get_position(self):
        """Get current position"""
        message = {
            "id": self.message_id,
            "method": "status.position",
            "params": {
                "targetID": self.target_id
            }
        }
        self.message_id += 1

        response = self.send_udp(message)
        return response.get('position')

    def get_info(self):
        """Get motor information"""
        message = {
            "id": self.message_id,
            "method": "status.info",
            "params": {
                "targetID": self.target_id
            }
        }
        self.message_id += 1

        response = self.send_udp(message)
        return response.get('info')

    def close(self):
        """Close connections"""
        if self.tcp_socket:
            self.tcp_socket.close()
        if self.udp_socket:
            self.udp_socket.close()


# Example usage
if __name__ == "__main__":
    # Initialize controller
    controller = SomfyPoEController("192.168.1.150", "1234")

    try:
        # Connect and authenticate
        controller.connect()
        if controller.authenticate() and controller.authorize():

            # Get motor information
            info = controller.get_info()
            print(f"Motor: {info}")

            # Get current position
            position = controller.get_position()
            print(f"Current position: {position}")

            # Move to 50%
            print("Moving to 50%...")
            controller.move_to_position(50)

            # Wait a bit
            import time
            time.sleep(2)

            # Get new position
            position = controller.get_position()
            print(f"New position: {position}")

    finally:
        controller.close()
```

### JavaScript/Node.js Example

```javascript
const tls = require('tls');
const dgram = require('dgram');
const crypto = require('crypto');

class SomfyPoEController {
    constructor(motorIp, pinCode) {
        this.motorIp = motorIp;
        this.pinCode = pinCode;
        this.tcpPort = 55056;
        this.udpPort = 55055;
        this.targetId = null;
        this.aesKey = null;
        this.tcpSocket = null;
        this.udpSocket = null;
        this.messageId = 1;
    }

    connect() {
        return new Promise((resolve, reject) => {
            const options = {
                host: this.motorIp,
                port: this.tcpPort,
                rejectUnauthorized: false
            };

            this.tcpSocket = tls.connect(options, () => {
                console.log(`Connected to ${this.motorIp}:${this.tcpPort}`);
                resolve();
            });

            this.tcpSocket.on('error', reject);
        });
    }

    sendTcp(message) {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify(message);
            this.tcpSocket.write(data);

            this.tcpSocket.once('data', (data) => {
                const response = JSON.parse(data.toString());
                resolve(response);
            });

            this.tcpSocket.once('error', reject);
        });
    }

    async authenticate() {
        const message = {
            id: this.messageId++,
            method: 'security.auth',
            params: {
                code: this.pinCode
            }
        };

        const response = await this.sendTcp(message);

        if (response.result) {
            this.targetId = response.targetID;
            console.log(`Authenticated! Target ID: ${this.targetId}`);
            return true;
        }

        console.log('Authentication failed!');
        return false;
    }

    async authorize() {
        const message = {
            id: this.messageId++,
            method: 'security.get'
        };

        const response = await this.sendTcp(message);

        if (response.result && response.key) {
            this.aesKey = Buffer.from(response.key);
            console.log(`Authorization successful! Key length: ${this.aesKey.length}`);

            // Setup UDP socket
            this.udpSocket = dgram.createSocket('udp4');
            return true;
        }

        console.log('Authorization failed!');
        return false;
    }

    encryptMessage(message) {
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-128-cbc', this.aesKey, iv);

        let encrypted = cipher.update(message, 'utf8');
        encrypted = Buffer.concat([encrypted, cipher.final()]);

        return Buffer.concat([iv, encrypted]);
    }

    decryptMessage(data) {
        const iv = data.slice(0, 16);
        const encrypted = data.slice(16);

        const decipher = crypto.createDecipheriv('aes-128-cbc', this.aesKey, iv);

        let decrypted = decipher.update(encrypted);
        decrypted = Buffer.concat([decrypted, decipher.final()]);

        return decrypted.toString('utf8');
    }

    sendUdp(message) {
        return new Promise((resolve, reject) => {
            const data = JSON.stringify(message);
            const encrypted = this.encryptMessage(data);

            this.udpSocket.send(encrypted, this.udpPort, this.motorIp, (err) => {
                if (err) reject(err);
            });

            const timeout = setTimeout(() => {
                reject(new Error('UDP response timeout'));
            }, 5000);

            this.udpSocket.once('message', (msg) => {
                clearTimeout(timeout);
                const decrypted = this.decryptMessage(msg);
                const response = JSON.parse(decrypted);
                resolve(response);
            });
        });
    }

    async moveToPosition(position) {
        const message = {
            id: this.messageId++,
            method: 'move.to',
            params: {
                targetID: this.targetId,
                position: position,
                seq: 1
            }
        };

        const response = await this.sendUdp(message);
        return response.result || false;
    }

    async getPosition() {
        const message = {
            id: this.messageId++,
            method: 'status.position',
            params: {
                targetID: this.targetId
            }
        };

        const response = await this.sendUdp(message);
        return response.position;
    }

    close() {
        if (this.tcpSocket) this.tcpSocket.end();
        if (this.udpSocket) this.udpSocket.close();
    }
}

// Example usage
(async () => {
    const controller = new SomfyPoEController('192.168.1.150', '1234');

    try {
        await controller.connect();

        if (await controller.authenticate() && await controller.authorize()) {
            const position = await controller.getPosition();
            console.log('Current position:', position);

            await controller.moveToPosition(50);
            console.log('Moved to 50%');
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        controller.close();
    }
})();
```

---

## Additional Notes

### Motor Discovery

To discover all Somfy PoE motors on your network:

1. Send broadcast UDP packet (encrypted with any motor's key, or after authentication)
2. Method: `status.ping` with targetID: `"*"`
3. All motors will respond with their targetID

### Heartbeat

After successful authorization, send periodic heartbeat messages (every 30 seconds recommended):

```json
{
  "id": 999,
  "method": "status.ping",
  "params": {
    "targetID": "4CC206:160D00"
  }
}
```

### Push Notifications

Motors may send unsolicited status updates via UDP (e.g., when position changes due to manual control). These follow the same encrypted UDP format.

### Sequence Numbers

The `seq` parameter in move commands is a sequence number. Increment for each new movement command to help the motor detect and ignore duplicate packets.

### Motor Label

**CRITICAL:** Do not discard the motor information labels! Each motor has a unique 4-digit PIN code printed on the label. This PIN is required for authentication and cannot be recovered if lost.

The label also contains:
- MAC address
- Target ID format
- QR code for quick setup

### Network Configuration

Motors support both DHCP and static IP configuration. For production deployments:
- Use DHCP reservations (MAC-based) or static IPs
- Document all motor IP addresses and target IDs
- Use the Config Tool or Web Interface to set network configuration

---

## Troubleshooting

### Common Issues

**Connection Refused:**
- Verify motor is powered and on same network
- Check firewall rules for ports 55055-55056
- Confirm PoE switch provides adequate power

**Authentication Failed:**
- Verify PIN code is correct (from motor label)
- Check TLS certificate if using mutual TLS
- Ensure motor hasn't been factory reset

**UDP Commands Not Working:**
- Confirm authorization completed successfully
- Verify AES key was received
- Check encryption/decryption implementation
- Ensure UDP port 55055 is not blocked

**Motor Not Responding:**
- Send heartbeat to check connection
- Verify targetID is correct
- Check motor LED status (see programming guides)
- Motor may be locked - check lock status

### LED Status Indicators

- **Green Solid (2s):** Power up
- **Green Blinking:** Communication active
- **Amber Solid:** Limits not set
- **Amber Blinks 2x:** Pushing IP to network
- **Red Solid:** Obstacle detected
- **Red Blinking:** Thermal protection
- **Red Blinks 2x:** Out of limits
- **Red Fast Blink:** No network/IP
- **Off:** Normal idle state (limits set)

---

## References

- Somfy PoE Motor Web Interface Programming Guide v1.3
- Somfy PoE Motor Config Tool Programming Guide v2.0
- Driver Scripts (decompiled reference implementation)
- IEEE 802.3at PoE+ Standard
- JSON-RPC 2.0 Specification (inspiration for message format)

---

## Legal Notice

This documentation is provided for educational and interoperability purposes. Somfy®, Sonesse®, and related trademarks are property of Somfy Systems, Inc. This is an unofficial reverse-engineered API documentation not endorsed by Somfy.

**Use at your own risk.** Improper use of this API may damage motors or void warranties. Always follow proper safety procedures when controlling motorized window treatments.

---

**Document prepared by:** Reverse engineering analysis of Somfy PoE Motor driver v1.2
**Contact Somfy Support:** (800) 22-SOMFY (76639) | www.somfysystems.com
