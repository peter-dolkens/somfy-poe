# Somfy PoE Motor - TLS Certificate Guide

## Overview

Somfy PoE motors use TLS/SSL for secure communication over TCP port 55056. This guide covers certificate requirements, generation, and configuration for authentication with the motors.

**Document Version:** 1.0
**Last Updated:** January 2026

---

## Table of Contents

1. [Certificate Architecture](#certificate-architecture)
2. [Security Model](#security-model)
3. [Motor Certificates](#motor-certificates)
4. [Client Certificates](#client-certificates)
5. [Certificate Generation](#certificate-generation)
6. [Installation and Configuration](#installation-and-configuration)
7. [Troubleshooting](#troubleshooting)

---

## Certificate Architecture

### Overview

The Somfy PoE system uses a multi-layer security approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: TLS/SSL Mutual Authentication (TCP Port 55056)     │
│          - Client presents certificate                       │
│          - Motor presents self-signed certificate            │
│                                                              │
│ Layer 2: PIN Authentication                                  │
│          - 4-digit PIN code (printed on motor label)         │
│                                                              │
│ Layer 3: AES-128 Session Key Exchange                        │
│          - Obtained via security.get method                  │
│          - Used for all UDP communications (Port 55055)      │
└─────────────────────────────────────────────────────────────┘
```

### Certificate Hierarchy

```
Somfy PoE CA (Root Certificate)
├── Motor Certificate (per motor, self-signed)
│   ├── Subject: CN=<motor-hostname>
│   └── Used for: Motor identification
└── Client Certificate (per client application)
    ├── Subject: CN=client_somfy_*
    └── Used for: Client authentication
```

---

## Security Model

### Authentication Flow

```
1. TCP Connection (Port 55056)
   ├── Client → Motor: ClientHello
   ├── Motor → Client: ServerHello + Certificate
   ├── Client → Motor: Certificate (optional)
   └── TLS Handshake Complete

2. PIN Authentication (JSON-RPC over TLS)
   ├── Client → Motor: {"method": "security.auth", "params": {"code": "1234"}}
   └── Motor → Client: {"result": true, "targetID": "4CC206:160D00"}

3. Key Exchange
   ├── Client → Motor: {"method": "security.get"}
   └── Motor → Client: {"result": true, "key": [16-byte array]}

4. UDP Commands (Port 55055)
   └── All messages encrypted with AES-128-CBC using session key
```

### Certificate Verification Modes

The motors support multiple certificate verification modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| **None** | No certificate validation | Testing, development |
| **Optional** | Accept any client certificate | Basic security |
| **Required** | Validate against trusted CA | Production deployment |

**Default Mode:** Optional (motors accept connections with or without client certificates)

---

## Motor Certificates

### Motor Certificate Characteristics

Each motor has a unique self-signed certificate:

- **Type:** Self-signed X.509
- **Key Algorithm:** RSA 2048-bit
- **Validity:** 10+ years
- **Subject:** CN=\<motor-hostname\>.local
- **Extensions:** SubjectAlternativeName with motor IP and MAC-based identifiers

### Example Motor Certificate

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: <unique-per-motor>
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: CN=sfy_poe_160d00.local
        Validity
            Not Before: Jan  1 00:00:00 2024 GMT
            Not After : Dec 31 23:59:59 2034 GMT
        Subject: CN=sfy_poe_160d00.local
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                RSA Public-Key: (2048 bit)
        X509v3 extensions:
            X509v3 Subject Alternative Name:
                DNS:sfy_poe_160d00.local
                IP Address:192.168.1.150
```

### Viewing Motor Certificate

You can inspect the motor's certificate using OpenSSL:

```bash
# View certificate details
echo | openssl s_client -connect 192.168.1.150:55056 -showcerts 2>/dev/null | \
    openssl x509 -text -noout

# Extract certificate to file
echo | openssl s_client -connect 192.168.1.150:55056 -showcerts 2>/dev/null | \
    sed -n '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' > motor_cert.pem
```

### Motor Certificate Trust

**Important:** Motor certificates are self-signed. Client applications must:

1. **Disable certificate validation** (development)
2. **Trust the specific motor certificate** (production)
3. **Trust the Somfy PoE CA** (if provided)

---

## Client Certificates

### Somfy's Reference Certificates

The official Somfy PoE Config Tool includes these certificates:

1. **client_somfy_configtool.pfx**
   - Purpose: Config Tool authentication
   - Format: PKCS#12 (.pfx)
   - Contains: Private key + certificate

2. **client_somfy_poemotor.pfx**
   - Purpose: Alternative client certificate
   - Format: PKCS#12 (.pfx)
   - Contains: Private key + certificate

3. **somfy_poe_ca.crt**
   - Purpose: Root CA certificate
   - Format: X.509 PEM (.crt)
   - Used to validate motor certificates (optional)

### Using Reference Certificates

You can extract the reference certificates from the Config Tool installer:

```bash
# Extract from installer (requires 7zip or similar)
7z x POEConfigTool_Package_v1.4.1.exe -o./extracted/

# Find certificates
find ./extracted -name "*.pfx" -o -name "*.crt"
```

**Note:** The reference certificates are for testing/development. For production, generate your own certificates.

---

## Certificate Generation

### Option 1: No Client Certificate (Simplest)

Most applications don't need client certificates. The motors accept connections without them:

```python
import ssl
import socket

# Create SSL context with no certificate validation
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Connect to motor
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = context.wrap_socket(sock, server_hostname='192.168.1.150')
ssl_sock.connect(('192.168.1.150', 55056))

# Now proceed with PIN authentication
```

**Pros:**
- Simplest approach
- No certificate management
- Works with all motors

**Cons:**
- No client authentication at TLS layer
- Relies solely on PIN security

### Option 2: Self-Signed Client Certificate

Generate a simple self-signed certificate for your application:

```bash
#!/bin/bash
# generate_client_cert.sh

# Configuration
CLIENT_NAME="my_home_automation"
DAYS_VALID=3650  # 10 years

# Generate private key
openssl genrsa -out client_key.pem 2048

# Generate certificate signing request
openssl req -new -key client_key.pem -out client.csr \
    -subj "/CN=${CLIENT_NAME}"

# Generate self-signed certificate
openssl x509 -req -days ${DAYS_VALID} \
    -in client.csr \
    -signkey client_key.pem \
    -out client_cert.pem

# Create PKCS#12 bundle (optional - for some applications)
openssl pkcs12 -export \
    -in client_cert.pem \
    -inkey client_key.pem \
    -out client_cert.pfx \
    -passout pass:

echo "Generated:"
echo "  - client_key.pem (private key)"
echo "  - client_cert.pem (certificate)"
echo "  - client_cert.pfx (PKCS#12 bundle)"
```

**Usage in Python:**

```python
import ssl
import socket

# Create SSL context with client certificate
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
context.load_cert_chain(certfile='client_cert.pem', keyfile='client_key.pem')

# Connect to motor
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = context.wrap_socket(sock, server_hostname='192.168.1.150')
ssl_sock.connect(('192.168.1.150', 55056))
```

### Option 3: Proper Certificate Authority (Production)

For production deployments, create a proper CA hierarchy:

#### Step 1: Create Root CA

```bash
#!/bin/bash
# 01_create_ca.sh

CA_NAME="Somfy PoE Home CA"
CA_DIR="./somfy_ca"

mkdir -p ${CA_DIR}/{certs,private,newcerts}
chmod 700 ${CA_DIR}/private
touch ${CA_DIR}/index.txt
echo 1000 > ${CA_DIR}/serial

# Generate CA private key
openssl genrsa -aes256 -out ${CA_DIR}/private/ca_key.pem 4096
chmod 400 ${CA_DIR}/private/ca_key.pem

# Generate CA certificate
openssl req -new -x509 -days 7300 -key ${CA_DIR}/private/ca_key.pem \
    -out ${CA_DIR}/certs/ca_cert.pem \
    -subj "/CN=${CA_NAME}"

echo "Root CA created:"
echo "  - ${CA_DIR}/private/ca_key.pem (KEEP SECURE!)"
echo "  - ${CA_DIR}/certs/ca_cert.pem"
```

#### Step 2: Create OpenSSL Configuration

```bash
# Create openssl.cnf for CA operations
cat > somfy_ca/openssl.cnf << 'EOF'
[ ca ]
default_ca = CA_default

[ CA_default ]
dir              = ./somfy_ca
certs            = $dir/certs
new_certs_dir    = $dir/newcerts
database         = $dir/index.txt
serial           = $dir/serial
private_key      = $dir/private/ca_key.pem
certificate      = $dir/certs/ca_cert.pem
default_md       = sha256
default_days     = 3650
policy           = policy_loose

[ policy_loose ]
countryName            = optional
stateOrProvinceName    = optional
localityName           = optional
organizationName       = optional
organizationalUnitName = optional
commonName             = supplied
emailAddress           = optional

[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
string_mask        = utf8only
default_md         = sha256

[ req_distinguished_name ]
commonName         = Common Name

[ v3_client ]
basicConstraints = CA:FALSE
nsCertType = client
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF
```

#### Step 3: Generate Client Certificate from CA

```bash
#!/bin/bash
# 02_create_client_cert.sh

CA_DIR="./somfy_ca"
CLIENT_NAME="my_client"

# Generate client private key
openssl genrsa -out ${CLIENT_NAME}_key.pem 2048

# Generate certificate signing request
openssl req -new -key ${CLIENT_NAME}_key.pem -out ${CLIENT_NAME}.csr \
    -subj "/CN=${CLIENT_NAME}"

# Sign with CA
openssl ca -config ${CA_DIR}/openssl.cnf \
    -in ${CLIENT_NAME}.csr \
    -out ${CLIENT_NAME}_cert.pem \
    -extensions v3_client \
    -batch

# Create PKCS#12 bundle
openssl pkcs12 -export \
    -in ${CLIENT_NAME}_cert.pem \
    -inkey ${CLIENT_NAME}_key.pem \
    -certfile ${CA_DIR}/certs/ca_cert.pem \
    -out ${CLIENT_NAME}.pfx \
    -passout pass:

echo "Generated:"
echo "  - ${CLIENT_NAME}_key.pem"
echo "  - ${CLIENT_NAME}_cert.pem"
echo "  - ${CLIENT_NAME}.pfx"
```

#### Step 4: Trust Motor Certificates (Optional)

If you want to validate motor certificates, add them to your CA:

```bash
#!/bin/bash
# 03_trust_motor.sh

MOTOR_IP="192.168.1.150"
MOTOR_HOSTNAME="sfy_poe_160d00"
CA_DIR="./somfy_ca"

# Download motor certificate
echo | openssl s_client -connect ${MOTOR_IP}:55056 -showcerts 2>/dev/null | \
    sed -n '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' > ${MOTOR_HOSTNAME}_cert.pem

# Copy to trusted certs
cp ${MOTOR_HOSTNAME}_cert.pem ${CA_DIR}/certs/

echo "Motor certificate saved to: ${CA_DIR}/certs/${MOTOR_HOSTNAME}_cert.pem"
```

### Option 4: Let's Encrypt (Advanced)

For internet-exposed deployments with public DNS:

```bash
#!/bin/bash
# Using certbot for Let's Encrypt

# This only works if your motors have public DNS records
# Not typical for local home automation setups

certbot certonly --standalone \
    -d motor1.yourdomain.com \
    -d motor2.yourdomain.com
```

**Note:** This is rarely needed for local Somfy PoE deployments.

---

## Installation and Configuration

### Python - Using Client Certificate

```python
import ssl
import socket
import json

class SecureSomfyConnection:
    """Somfy PoE connection with TLS client certificate"""

    def __init__(self, motor_ip, pin_code, cert_file=None, key_file=None):
        self.motor_ip = motor_ip
        self.pin_code = pin_code
        self.cert_file = cert_file
        self.key_file = key_file
        self.tcp_socket = None

    def connect(self):
        """Establish secure TLS connection"""
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Load client certificate if provided
        if self.cert_file and self.key_file:
            context.load_cert_chain(
                certfile=self.cert_file,
                keyfile=self.key_file
            )
            print("Using client certificate authentication")

        # Create and wrap socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket = context.wrap_socket(sock, server_hostname=self.motor_ip)
        self.tcp_socket.connect((self.motor_ip, 55056))

        print(f"TLS connection established to {self.motor_ip}:55056")

        # Check peer certificate
        peer_cert = self.tcp_socket.getpeercert()
        print(f"Motor certificate: {peer_cert.get('subject', 'N/A')}")

    def authenticate(self):
        """Authenticate with PIN"""
        message = {
            "id": 1,
            "method": "security.auth",
            "params": {"code": self.pin_code}
        }

        self.tcp_socket.sendall(json.dumps(message).encode('utf-8'))
        response = json.loads(self.tcp_socket.recv(4096).decode('utf-8'))

        if response.get('result'):
            print(f"Authentication successful: {response.get('targetID')}")
            return True
        else:
            print("Authentication failed")
            return False

    def close(self):
        """Close connection"""
        if self.tcp_socket:
            self.tcp_socket.close()

# Example usage with certificate
conn = SecureSomfyConnection(
    motor_ip="192.168.1.150",
    pin_code="1234",
    cert_file="client_cert.pem",
    key_file="client_key.pem"
)

try:
    conn.connect()
    conn.authenticate()
finally:
    conn.close()

# Example usage without certificate
conn_simple = SecureSomfyConnection(
    motor_ip="192.168.1.150",
    pin_code="1234"
)

try:
    conn_simple.connect()
    conn_simple.authenticate()
finally:
    conn_simple.close()
```

### Node.js - Using Client Certificate

```javascript
const tls = require('tls');
const fs = require('fs');

class SecureSomfyConnection {
    constructor(motorIp, pinCode, certFile = null, keyFile = null) {
        this.motorIp = motorIp;
        this.pinCode = pinCode;
        this.certFile = certFile;
        this.keyFile = keyFile;
        this.socket = null;
    }

    connect() {
        return new Promise((resolve, reject) => {
            const options = {
                host: this.motorIp,
                port: 55056,
                rejectUnauthorized: false
            };

            // Add client certificate if provided
            if (this.certFile && this.keyFile) {
                options.cert = fs.readFileSync(this.certFile);
                options.key = fs.readFileSync(this.keyFile);
                console.log('Using client certificate authentication');
            }

            this.socket = tls.connect(options, () => {
                console.log(`TLS connection established to ${this.motorIp}:55056`);
                console.log('Authorized:', this.socket.authorized);
                resolve();
            });

            this.socket.on('error', reject);
        });
    }

    authenticate() {
        return new Promise((resolve, reject) => {
            const message = {
                id: 1,
                method: 'security.auth',
                params: { code: this.pinCode }
            };

            this.socket.write(JSON.stringify(message));

            this.socket.once('data', (data) => {
                const response = JSON.parse(data.toString());
                if (response.result) {
                    console.log(`Authentication successful: ${response.targetID}`);
                    resolve(response);
                } else {
                    reject(new Error('Authentication failed'));
                }
            });

            this.socket.once('error', reject);
        });
    }

    close() {
        if (this.socket) {
            this.socket.end();
        }
    }
}

// Example usage with certificate
(async () => {
    const conn = new SecureSomfyConnection(
        '192.168.1.150',
        '1234',
        'client_cert.pem',
        'client_key.pem'
    );

    try {
        await conn.connect();
        await conn.authenticate();
    } catch (error) {
        console.error('Error:', error);
    } finally {
        conn.close();
    }
})();
```

### Go - Using Client Certificate

```go
package main

import (
    "crypto/tls"
    "crypto/x509"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "log"
)

type SecureSomfyConnection struct {
    MotorIP  string
    PinCode  string
    CertFile string
    KeyFile  string
    conn     *tls.Conn
}

func (s *SecureSomfyConnection) Connect() error {
    // Create TLS configuration
    config := &tls.Config{
        InsecureSkipVerify: true, // Skip motor certificate verification
    }

    // Load client certificate if provided
    if s.CertFile != "" && s.KeyFile != "" {
        cert, err := tls.LoadX509KeyPair(s.CertFile, s.KeyFile)
        if err != nil {
            return fmt.Errorf("failed to load certificate: %v", err)
        }
        config.Certificates = []tls.Certificate{cert}
        log.Println("Using client certificate authentication")
    }

    // Connect
    conn, err := tls.Dial("tcp", fmt.Sprintf("%s:55056", s.MotorIP), config)
    if err != nil {
        return fmt.Errorf("connection failed: %v", err)
    }

    s.conn = conn
    log.Printf("TLS connection established to %s:55056", s.MotorIP)

    return nil
}

func (s *SecureSomfyConnection) Authenticate() error {
    message := map[string]interface{}{
        "id":     1,
        "method": "security.auth",
        "params": map[string]string{
            "code": s.PinCode,
        },
    }

    // Send authentication request
    data, _ := json.Marshal(message)
    _, err := s.conn.Write(data)
    if err != nil {
        return err
    }

    // Read response
    buffer := make([]byte, 4096)
    n, err := s.conn.Read(buffer)
    if err != nil {
        return err
    }

    var response map[string]interface{}
    json.Unmarshal(buffer[:n], &response)

    if result, ok := response["result"].(bool); ok && result {
        log.Printf("Authentication successful: %v", response["targetID"])
        return nil
    }

    return fmt.Errorf("authentication failed")
}

func (s *SecureSomfyConnection) Close() {
    if s.conn != nil {
        s.conn.Close()
    }
}

func main() {
    conn := &SecureSomfyConnection{
        MotorIP:  "192.168.1.150",
        PinCode:  "1234",
        CertFile: "client_cert.pem",
        KeyFile:  "client_key.pem",
    }

    if err := conn.Connect(); err != nil {
        log.Fatal(err)
    }
    defer conn.Close()

    if err := conn.Authenticate(); err != nil {
        log.Fatal(err)
    }
}
```

---

## Troubleshooting

### Common Certificate Errors

#### Error: "certificate verify failed"

**Cause:** Client is trying to verify the motor's self-signed certificate

**Solution:**

```python
# Disable certificate verification
context.verify_mode = ssl.CERT_NONE
context.check_hostname = False
```

#### Error: "SSL handshake failed"

**Causes:**
1. Wrong port (ensure using 55056)
2. TLS version mismatch
3. Cipher suite incompatibility

**Solutions:**

```python
# Try different TLS versions
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
# or
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
```

#### Error: "PEM routines:PEM_read_bio:no start line"

**Cause:** Invalid certificate file format

**Solution:**

```bash
# Verify certificate format
openssl x509 -in client_cert.pem -text -noout

# Convert DER to PEM if needed
openssl x509 -inform DER -in cert.der -out cert.pem
```

### Debugging TLS Connections

#### Using OpenSSL Command Line

```bash
# Test connection without certificate
openssl s_client -connect 192.168.1.150:55056 -showcerts

# Test with client certificate
openssl s_client -connect 192.168.1.150:55056 \
    -cert client_cert.pem \
    -key client_key.pem \
    -showcerts

# Test with specific TLS version
openssl s_client -connect 192.168.1.150:55056 \
    -tls1_2 \
    -showcerts

# Show supported cipher suites
openssl s_client -connect 192.168.1.150:55056 -cipher 'ALL'
```

#### Using curl

```bash
# Test HTTPS connection
curl -k https://192.168.1.150:55056/

# With client certificate
curl -k --cert client_cert.pem --key client_key.pem \
    https://192.168.1.150:55056/

# Verbose output
curl -v -k https://192.168.1.150:55056/
```

### Certificate Validation in Python

```python
import ssl
import socket
from pprint import pprint

def inspect_motor_certificate(motor_ip, port=55056):
    """Inspect and print motor certificate details"""

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = context.wrap_socket(sock, server_hostname=motor_ip)

    try:
        ssl_sock.connect((motor_ip, port))

        # Get peer certificate
        cert = ssl_sock.getpeercert()

        print("=== Motor Certificate Information ===")
        print(f"\nSubject:")
        pprint(cert.get('subject', 'N/A'))

        print(f"\nIssuer:")
        pprint(cert.get('issuer', 'N/A'))

        print(f"\nVersion: {cert.get('version', 'N/A')}")
        print(f"Serial Number: {cert.get('serialNumber', 'N/A')}")

        print(f"\nNot Before: {cert.get('notBefore', 'N/A')}")
        print(f"Not After: {cert.get('notAfter', 'N/A')}")

        print(f"\nSubject Alt Names:")
        pprint(cert.get('subjectAltName', []))

        # Get cipher suite
        print(f"\nCipher Suite: {ssl_sock.cipher()}")

        # Get TLS version
        print(f"TLS Version: {ssl_sock.version()}")

    finally:
        ssl_sock.close()

# Example usage
inspect_motor_certificate("192.168.1.150")
```

---

## Best Practices

### Development

1. **Start Simple:** Begin without client certificates
2. **Disable Validation:** Use `CERT_NONE` for motor certificates
3. **Test Locally:** Verify connectivity before adding certificates
4. **Log Everything:** Enable verbose SSL logging during development

### Production

1. **Use Client Certificates:** Adds extra authentication layer
2. **Secure Private Keys:** Store with appropriate file permissions (600)
3. **Rotate Certificates:** Plan for certificate renewal before expiry
4. **Monitor Expiry:** Alert when certificates approach expiration
5. **Document Configuration:** Keep record of all certificates and their purposes

### Security

1. **Never Commit Private Keys:** Add `*.pem`, `*.pfx`, `*.key` to `.gitignore`
2. **Use Strong Passwords:** If encrypting private keys, use strong passphrases
3. **Limit Certificate Access:** Only authorized applications should have certificates
4. **Separate Environments:** Different certificates for dev/staging/production
5. **PIN Protection:** The 4-digit PIN is the primary security - protect it

### Certificate Storage

```bash
# Recommended file permissions
chmod 600 client_key.pem         # Private key - owner read/write only
chmod 644 client_cert.pem        # Certificate - readable by all
chmod 644 ca_cert.pem            # CA certificate - readable by all

# Store in secure location
/etc/somfy/certs/                # System-wide
~/.config/somfy/certs/           # User-specific
/opt/homeautomation/certs/       # Application-specific
```

---

## Complete Example: Certificate-Based Authentication System

```python
#!/usr/bin/env python3
"""
Complete Somfy PoE authentication system with certificate management
"""

import ssl
import socket
import json
import os
from pathlib import Path

class SomfyCertificateManager:
    """Manages certificates for Somfy PoE connections"""

    def __init__(self, cert_dir="./certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)

    def generate_client_cert(self, client_name="somfy_client"):
        """Generate a self-signed client certificate"""
        import subprocess

        key_file = self.cert_dir / f"{client_name}_key.pem"
        cert_file = self.cert_dir / f"{client_name}_cert.pem"

        if key_file.exists() and cert_file.exists():
            print(f"Certificate already exists: {cert_file}")
            return str(cert_file), str(key_file)

        # Generate private key
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(key_file),
            "2048"
        ], check=True)

        # Generate certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509",
            "-key", str(key_file),
            "-out", str(cert_file),
            "-days", "3650",
            "-subj", f"/CN={client_name}"
        ], check=True)

        # Set permissions
        os.chmod(key_file, 0o600)
        os.chmod(cert_file, 0o644)

        print(f"Generated certificate: {cert_file}")
        return str(cert_file), str(key_file)

    def save_motor_cert(self, motor_ip, motor_name):
        """Download and save motor certificate"""
        cert_file = self.cert_dir / f"motor_{motor_name}_cert.pem"

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_sock = context.wrap_socket(sock)

        try:
            ssl_sock.connect((motor_ip, 55056))
            cert_der = ssl_sock.getpeercert(binary_form=True)

            # Convert DER to PEM
            import ssl as ssl_lib
            cert_pem = ssl_lib.DER_cert_to_PEM_cert(cert_der)

            with open(cert_file, 'w') as f:
                f.write(cert_pem)

            print(f"Saved motor certificate: {cert_file}")
            return str(cert_file)

        finally:
            ssl_sock.close()

class SecureSomfyClient:
    """Somfy PoE client with certificate support"""

    def __init__(self, motor_ip, pin_code, cert_manager=None):
        self.motor_ip = motor_ip
        self.pin_code = pin_code
        self.cert_manager = cert_manager or SomfyCertificateManager()
        self.socket = None
        self.target_id = None

    def connect(self, use_client_cert=True):
        """Connect with optional client certificate"""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        if use_client_cert:
            try:
                cert_file, key_file = self.cert_manager.generate_client_cert()
                context.load_cert_chain(cert_file, key_file)
                print("✓ Using client certificate")
            except Exception as e:
                print(f"⚠ Client certificate failed: {e}")
                print("  Connecting without client certificate")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = context.wrap_socket(sock, server_hostname=self.motor_ip)
        self.socket.connect((self.motor_ip, 55056))

        print(f"✓ TLS connection established to {self.motor_ip}")

    def authenticate(self):
        """Authenticate with PIN"""
        message = {
            "id": 1,
            "method": "security.auth",
            "params": {"code": self.pin_code}
        }

        self.socket.sendall(json.dumps(message).encode('utf-8'))
        response = json.loads(self.socket.recv(4096).decode('utf-8'))

        if response.get('result'):
            self.target_id = response.get('targetID')
            print(f"✓ Authentication successful: {self.target_id}")
            return True
        else:
            print("✗ Authentication failed")
            return False

    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()

# Example usage
if __name__ == "__main__":
    # Initialize certificate manager
    cert_mgr = SomfyCertificateManager(cert_dir="./somfy_certs")

    # Create client
    client = SecureSomfyClient(
        motor_ip="192.168.1.150",
        pin_code="1234",
        cert_manager=cert_mgr
    )

    try:
        # Connect with certificate
        client.connect(use_client_cert=True)

        # Authenticate
        if client.authenticate():
            print("\n✓ Ready to send motor commands")

            # Optional: Save motor certificate for reference
            cert_mgr.save_motor_cert("192.168.1.150", "living_room")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()
```

---

## References

- **OpenSSL Documentation:** https://www.openssl.org/docs/
- **Python SSL Module:** https://docs.python.org/3/library/ssl.html
- **Node.js TLS Module:** https://nodejs.org/api/tls.html
- **X.509 Certificates:** RFC 5280
- **TLS 1.2:** RFC 5246
- **TLS 1.3:** RFC 8446

---

**Document prepared by:** Analysis of Somfy PoE Config Tool and protocol reverse engineering
**Contact Somfy Support:** (800) 22-SOMFY (76639) | www.somfysystems.com
