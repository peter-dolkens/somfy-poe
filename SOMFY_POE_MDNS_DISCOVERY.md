# Somfy PoE Motor - mDNS/Bonjour Discovery

## Overview

Somfy PoE motors support automatic network discovery using mDNS (Multicast DNS), commonly known as Bonjour on Apple platforms. This allows applications to automatically find motors on the local network without requiring manual IP address configuration.

**Document Version:** 1.0
**Last Updated:** January 2026

---

## Table of Contents

1. [Introduction to mDNS](#introduction-to-mdns)
2. [Service Advertisement](#service-advertisement)
3. [Discovery Methods](#discovery-methods)
4. [Implementation Examples](#implementation-examples)
5. [Troubleshooting](#troubleshooting)

---

## Introduction to mDNS

### What is mDNS?

Multicast DNS (mDNS) is a protocol that resolves hostnames to IP addresses within small networks without requiring a centralized DNS server. It operates on:

- **Multicast Address:** 224.0.0.251 (IPv4) or FF02::FB (IPv6)
- **Port:** 5353 (UDP)
- **Standard:** RFC 6762

### Benefits for Somfy PoE Motors

- **Zero Configuration:** Motors automatically advertise their presence
- **Dynamic IP Support:** Works with DHCP without tracking IP changes
- **Easy Discovery:** Applications can find all motors instantly
- **Human-Readable Names:** Motors use `.local` domain names

---

## Service Advertisement

### Hostname Format

Each Somfy PoE motor advertises itself with a hostname based on its MAC address:

```
sfy_poe_<last_6_hex_digits>.local
```

**Example:**
- MAC Address: `4C:C2:06:16:0D:00`
- Hostname: `sfy_poe_160d00.local`

### Service Type

Somfy PoE motors advertise as:

```
_somfy-poe._tcp.local.
```

### TXT Record Contents

The mDNS TXT record contains key-value pairs with motor information:

```
txtvers=1
model=Sonesse 30 PoE
mac=4CC206160D00
targetid=4CC206:160D00
firmware=1.2.0
hardware=1.0
name=Living Room Shade
```

**Field Descriptions:**

| Field | Description | Example |
|-------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `model` | Motor model name | `Sonesse 30 PoE`, `Sonesse 40 PoE` |
| `mac` | MAC address (no colons) | `4CC206160D00` |
| `targetid` | API target identifier | `4CC206:160D00` |
| `firmware` | Firmware version | `1.2.0` |
| `hardware` | Hardware version | `1.0` |
| `name` | User-assigned motor name | `Living Room Shade` |

---

## Discovery Methods

### Method 1: Using System mDNS Tools

#### macOS/Linux - dns-sd

Query for Somfy PoE motors:

```bash
# Browse for Somfy PoE services
dns-sd -B _somfy-poe._tcp local.

# Lookup specific motor
dns-sd -L "sfy_poe_160d00" _somfy-poe._tcp local.

# Resolve hostname to IP
dns-sd -G v4 sfy_poe_160d00.local
```

#### Linux - avahi-browse

```bash
# Browse for services
avahi-browse -t _somfy-poe._tcp

# Resolve service details
avahi-browse -t _somfy-poe._tcp -r

# Resolve hostname
avahi-resolve -n sfy_poe_160d00.local
```

#### Windows - dns-sd.exe (Bonjour SDK)

```cmd
REM Browse for services
dns-sd.exe -B _somfy-poe._tcp local.

REM Lookup specific motor
dns-sd.exe -L "sfy_poe_160d00" _somfy-poe._tcp local.
```

### Method 2: Direct Hostname Resolution

Most modern operating systems support `.local` hostname resolution automatically:

```bash
# Ping motor by hostname
ping sfy_poe_160d00.local

# Connect to motor
curl -k https://sfy_poe_160d00.local:55056
```

---

## Implementation Examples

### Python - Using zeroconf Library

```python
#!/usr/bin/env python3
"""
Somfy PoE Motor Discovery using mDNS
"""

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import socket
import time

class SomfyMotorListener(ServiceListener):
    """Listener for Somfy PoE motor discoveries"""

    def __init__(self):
        self.motors = {}

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is discovered"""
        info = zc.get_service_info(type_, name)
        if info:
            # Extract motor information
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]

            # Parse TXT record
            properties = {}
            if info.properties:
                for key, value in info.properties.items():
                    try:
                        properties[key.decode('utf-8')] = value.decode('utf-8')
                    except:
                        properties[key.decode('utf-8')] = value

            motor_info = {
                'name': name,
                'hostname': info.server,
                'addresses': addresses,
                'port': info.port,
                'properties': properties
            }

            self.motors[name] = motor_info

            print(f"\n[DISCOVERED] {name}")
            print(f"  Hostname: {info.server}")
            print(f"  IP Address: {', '.join(addresses)}")
            print(f"  Port: {info.port}")
            print(f"  Model: {properties.get('model', 'Unknown')}")
            print(f"  MAC: {properties.get('mac', 'Unknown')}")
            print(f"  Target ID: {properties.get('targetid', 'Unknown')}")
            print(f"  Firmware: {properties.get('firmware', 'Unknown')}")
            print(f"  Motor Name: {properties.get('name', 'Unnamed')}")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed"""
        if name in self.motors:
            print(f"\n[REMOVED] {name}")
            del self.motors[name]

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated"""
        print(f"\n[UPDATED] {name}")
        self.add_service(zc, type_, name)

def discover_motors(timeout=10):
    """
    Discover Somfy PoE motors on the local network

    Args:
        timeout: Discovery duration in seconds

    Returns:
        Dictionary of discovered motors
    """
    print(f"Scanning for Somfy PoE motors ({timeout} seconds)...")

    zeroconf = Zeroconf()
    listener = SomfyMotorListener()
    browser = ServiceBrowser(zeroconf, "_somfy-poe._tcp.local.", listener)

    try:
        time.sleep(timeout)
    finally:
        zeroconf.close()

    return listener.motors

def resolve_hostname(hostname):
    """
    Resolve a .local hostname to IP address

    Args:
        hostname: Hostname to resolve (e.g., 'sfy_poe_160d00.local')

    Returns:
        IP address string or None
    """
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None

# Example usage
if __name__ == "__main__":
    # Discover all motors
    motors = discover_motors(timeout=10)

    print(f"\n{'='*60}")
    print(f"Discovery complete. Found {len(motors)} motor(s)")
    print(f"{'='*60}")

    # Resolve a specific hostname
    hostname = "sfy_poe_160d00.local"
    ip = resolve_hostname(hostname)
    if ip:
        print(f"\nResolved {hostname} to {ip}")
    else:
        print(f"\nCould not resolve {hostname}")
```

**Install dependencies:**

```bash
pip install zeroconf
```

### Node.js - Using bonjour-hap Library

```javascript
#!/usr/bin/env node
/**
 * Somfy PoE Motor Discovery using mDNS
 */

const bonjour = require('bonjour-hap')();

const DISCOVERY_TIMEOUT = 10000; // 10 seconds

console.log(`Scanning for Somfy PoE motors (${DISCOVERY_TIMEOUT/1000} seconds)...`);

const motors = {};

// Browse for Somfy PoE services
const browser = bonjour.find({ type: 'somfy-poe' }, (service) => {
    const motorInfo = {
        name: service.name,
        hostname: service.host,
        addresses: service.addresses || [],
        port: service.port,
        type: service.type,
        txt: service.txt || {}
    };

    motors[service.name] = motorInfo;

    console.log('\n[DISCOVERED]', service.name);
    console.log('  Hostname:', service.host);
    console.log('  IP Address:', service.addresses?.join(', ') || 'N/A');
    console.log('  Port:', service.port);
    console.log('  Model:', service.txt?.model || 'Unknown');
    console.log('  MAC:', service.txt?.mac || 'Unknown');
    console.log('  Target ID:', service.txt?.targetid || 'Unknown');
    console.log('  Firmware:', service.txt?.firmware || 'Unknown');
    console.log('  Motor Name:', service.txt?.name || 'Unnamed');
});

// Stop discovery after timeout
setTimeout(() => {
    browser.stop();

    console.log('\n' + '='.repeat(60));
    console.log(`Discovery complete. Found ${Object.keys(motors).length} motor(s)`);
    console.log('='.repeat(60));

    // Clean up
    bonjour.destroy();
}, DISCOVERY_TIMEOUT);

// Handle service removal
browser.on('down', (service) => {
    console.log('\n[REMOVED]', service.name);
    delete motors[service.name];
});
```

**Install dependencies:**

```bash
npm install bonjour-hap
```

### Python - Simple DNS Resolver Only

If you only need to resolve hostnames without service browsing:

```python
import socket

def resolve_motor_hostname(hostname):
    """
    Resolve a Somfy motor .local hostname

    Args:
        hostname: Motor hostname (e.g., 'sfy_poe_160d00.local')

    Returns:
        IP address string or None
    """
    try:
        # This works on systems with mDNS support (macOS, Linux with Avahi)
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror as e:
        print(f"Error resolving {hostname}: {e}")
        return None

# Example usage
motors = [
    'sfy_poe_160d00.local',
    'sfy_poe_160d01.local',
    'sfy_poe_160d02.local'
]

for hostname in motors:
    ip = resolve_motor_hostname(hostname)
    if ip:
        print(f"{hostname} -> {ip}")
    else:
        print(f"{hostname} -> Could not resolve")
```

### Go - Using hashicorp/mdns

```go
package main

import (
    "fmt"
    "log"
    "time"

    "github.com/hashicorp/mdns"
)

// SomfyMotor represents a discovered motor
type SomfyMotor struct {
    Name      string
    Hostname  string
    IPAddress string
    Port      int
    TXT       map[string]string
}

func discoverMotors(timeout time.Duration) ([]*SomfyMotor, error) {
    motors := make([]*SomfyMotor, 0)

    // Create channel for results
    entriesCh := make(chan *mdns.ServiceEntry, 10)

    // Start discovery
    go func() {
        if err := mdns.Lookup("_somfy-poe._tcp", entriesCh); err != nil {
            log.Printf("Discovery error: %v", err)
        }
        close(entriesCh)
    }()

    // Collect results with timeout
    timer := time.After(timeout)

    for {
        select {
        case entry := <-entriesCh:
            if entry == nil {
                return motors, nil
            }

            // Parse TXT records
            txt := make(map[string]string)
            for _, field := range entry.InfoFields {
                // Parse key=value pairs
                // (simplified - production code should handle edge cases)
                txt[field] = field
            }

            motor := &SomfyMotor{
                Name:      entry.Name,
                Hostname:  entry.Host,
                IPAddress: entry.AddrV4.String(),
                Port:      entry.Port,
                TXT:       txt,
            }

            motors = append(motors, motor)

            fmt.Printf("\n[DISCOVERED] %s\n", entry.Name)
            fmt.Printf("  Hostname: %s\n", entry.Host)
            fmt.Printf("  IP: %s\n", entry.AddrV4)
            fmt.Printf("  Port: %d\n", entry.Port)

        case <-timer:
            return motors, nil
        }
    }
}

func main() {
    fmt.Println("Scanning for Somfy PoE motors (10 seconds)...")

    motors, err := discoverMotors(10 * time.Second)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("\n%s\n", "==============================================")
    fmt.Printf("Discovery complete. Found %d motor(s)\n", len(motors))
    fmt.Printf("%s\n", "==============================================")
}
```

**Install dependencies:**

```bash
go get github.com/hashicorp/mdns
```

---

## Troubleshooting

### Motors Not Discovered

**Check mDNS Service:**

```bash
# macOS - Check mDNSResponder is running
sudo launchctl list | grep mDNSResponder

# Linux - Check Avahi daemon
systemctl status avahi-daemon

# Windows - Check Bonjour Service
sc query "Bonjour Service"
```

**Common Issues:**

1. **Firewall Blocking mDNS:**
   - Allow UDP port 5353 and multicast to 224.0.0.251
   - On Linux: `sudo ufw allow 5353/udp`

2. **Network Segmentation:**
   - mDNS doesn't cross routers/subnets by default
   - Ensure discovery device is on same subnet as motors

3. **Bonjour Not Installed (Windows):**
   - Install Apple Bonjour for Windows
   - Or use Bonjour SDK for development

4. **IPv6 vs IPv4:**
   - Some systems prefer IPv6, motors may only advertise IPv4
   - Explicitly request IPv4 resolution

### Verify Network Connectivity

```bash
# Test multicast reception
ping 224.0.0.251

# Check motor is reachable
ping sfy_poe_160d00.local

# Test direct connection
curl -k https://sfy_poe_160d00.local:55056
```

### Debug mDNS Traffic

#### Using tcpdump

```bash
# Capture mDNS traffic
sudo tcpdump -i any port 5353 -vv

# Look for Somfy PoE announcements
sudo tcpdump -i any port 5353 -vv | grep -i somfy
```

#### Using Wireshark

1. Start capture on your network interface
2. Filter: `udp.port == 5353`
3. Look for DNS (multicast) packets with `_somfy-poe._tcp.local`

### Manual Query

Use `dig` or `nslookup` with mDNS:

```bash
# Query for service records
dig @224.0.0.251 -p 5353 _somfy-poe._tcp.local PTR

# Query for specific hostname
dig @224.0.0.251 -p 5353 sfy_poe_160d00.local A
```

---

## Best Practices

### For Application Developers

1. **Cache Results:** Store discovered motors to avoid repeated scans
2. **Handle Updates:** Listen for service updates when motors change IP
3. **Fallback to IP:** Support manual IP entry if mDNS fails
4. **Background Discovery:** Don't block UI during discovery
5. **Timeout Appropriately:** 5-10 seconds is usually sufficient

### For Network Administrators

1. **Enable mDNS:** Ensure mDNS/Bonjour is enabled on network
2. **Multicast Support:** Verify switches support multicast
3. **Same Subnet:** Keep motors and controllers on same subnet
4. **Firewall Rules:** Allow UDP 5353 for mDNS
5. **QoS:** Consider QoS rules for PoE motor traffic

### For Home Automation Integration

1. **Initial Discovery:** Run discovery on startup
2. **Periodic Refresh:** Re-scan every 5-10 minutes to catch new motors
3. **Hostname Preference:** Use `.local` hostnames instead of IPs when possible
4. **Graceful Degradation:** Fall back to IP if hostname resolution fails
5. **User Override:** Allow users to manually configure motors

---

## Integration with Somfy PoE API

### Complete Discovery and Connection Flow

```python
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import socket
import ssl
import json
import time

class SomfyDiscoveryController:
    """Discovers and connects to Somfy PoE motors"""

    def __init__(self):
        self.motors = {}
        self.zeroconf = None

    def discover(self, timeout=10):
        """Discover motors via mDNS"""
        listener = self._create_listener()
        self.zeroconf = Zeroconf()
        browser = ServiceBrowser(self.zeroconf, "_somfy-poe._tcp.local.", listener)

        time.sleep(timeout)
        return self.motors

    def _create_listener(self):
        """Create mDNS service listener"""
        parent = self

        class Listener(ServiceListener):
            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if info:
                    motor_ip = socket.inet_ntoa(info.addresses[0])
                    properties = {}
                    if info.properties:
                        for k, v in info.properties.items():
                            properties[k.decode('utf-8')] = v.decode('utf-8')

                    parent.motors[name] = {
                        'ip': motor_ip,
                        'hostname': info.server,
                        'targetID': properties.get('targetid'),
                        'model': properties.get('model'),
                        'name': properties.get('name', 'Unnamed')
                    }

        return Listener()

    def connect_to_motor(self, motor_name, pin_code):
        """Connect to discovered motor using API"""
        if motor_name not in self.motors:
            raise ValueError(f"Motor {motor_name} not found")

        motor = self.motors[motor_name]

        # Use hostname or IP
        host = motor['hostname'].rstrip('.') or motor['ip']

        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Connect via TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        ssl_sock.connect((motor['ip'], 55056))

        # Authenticate
        auth_msg = {
            "id": 1,
            "method": "security.auth",
            "params": {"code": pin_code}
        }

        ssl_sock.sendall(json.dumps(auth_msg).encode('utf-8'))
        response = json.loads(ssl_sock.recv(4096).decode('utf-8'))

        if response.get('result'):
            print(f"Connected to {motor['name']} (Target ID: {motor['targetID']})")
            return ssl_sock
        else:
            raise Exception("Authentication failed")

    def cleanup(self):
        """Clean up mDNS resources"""
        if self.zeroconf:
            self.zeroconf.close()

# Example usage
controller = SomfyDiscoveryController()
motors = controller.discover(timeout=10)

print(f"Found {len(motors)} motor(s)")

# Connect to first motor
if motors:
    motor_name = list(motors.keys())[0]
    try:
        conn = controller.connect_to_motor(motor_name, "1234")
        # Now use connection for API commands
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

controller.cleanup()
```

---

## References

- **mDNS RFC:** RFC 6762 - Multicast DNS
- **DNS-SD RFC:** RFC 6763 - DNS-Based Service Discovery
- **Apple Bonjour:** https://developer.apple.com/bonjour/
- **Avahi (Linux):** https://www.avahi.org/
- **zeroconf Python:** https://github.com/jstasiak/python-zeroconf

---

**Document prepared by:** Reverse engineering analysis of Somfy PoE Config Tool
**Contact Somfy Support:** (800) 22-SOMFY (76639) | www.somfysystems.com
