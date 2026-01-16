# Driver Format Documentation

## Overview

Driver files are **Microsoft OLE/Composite Document Files** (CFB format) that contain embedded JavaScript driver scripts and resources.

## File Structure

- **Format**: OLE/CFB (Compound File Binary) - Microsoft's structured storage format
- **Contents**: Multiple embedded JavaScript files and resources (certificates, keys, etc.)
- **Compression**: Individual scripts are compressed using **zlib/deflate** compression

## Extraction Process

### 1. Extract OLE Streams

The driver file is a compound document containing multiple streams. You can extract these using tools like:
- `oledump.py` (Python)
- `ssconvert` (Gnumeric)
- Custom OLE parsers

### 2. Decompress Scripts

Each extracted stream is zlib-compressed:

**Magic Bytes**: `78 da` (zlib header)

**Decompression**: Use zlib inflate to decompress:

```python
import zlib

with open('script.bin', 'rb') as f:
    compressed_data = f.read()

decompressed = zlib.decompress(compressed_data)

with open('script.js', 'wb') as f:
    f.write(decompressed)
```

Or using command line:
```bash
# Using openssl
openssl zlib -d -in script.bin -out script.js

# Using Python one-liner
python3 -c "import sys,zlib; sys.stdout.buffer.write(zlib.decompress(sys.stdin.buffer.read()))" < script.bin > script.js
```

## Extracted Files

The driver contains 25 scripts organized as follows:

### Core Infrastructure (1-5)
1. **Polyfill.js** - JavaScript polyfills for missing features
2. **Utilities.js** - Utility functions
3. **DebugUtil.js** - Debugging utilities
4. **PriorityCommUtil.js** - Priority-based communication queue
5. **Registrar.js** - Component registration system

### Interfaces (6-12)
6. **IResponseHandler.js** - Response handler interface
7. **IInitializable.js** - Initialization interface
8. **IPollable.js** - Polling interface
9. **IGroup.js** - Group interface
10. **IProcessor.js** - Processor interface
11. **IComponent.js** - Component interface
12. **IComponentState.js** - Component state interface

### Protocol/Messaging (13-19)
13. **CommandMessage.js** - Command message structure
14. **CommandParameters.js** - Command parameters
15. **CommandRequest.js** - Command request handling
16. **ErrorParameters.js** - Error parameter handling
17. **ResponseMessage.js** - Response message parsing
18. **ResponseParameters.js** - Response parameters
19. **ProtocolUtil.js** - Protocol utilities

### Components (20-23)
20. **Component.js** - Base component class
21. **MotorComponent.js** - Motor-specific component
22. **GroupComponent.js** - Group handling component
23. **SomfyPOEMotor.js** - Main driver implementation (largest file ~42KB decompressed)

### Resources (24-25)
1.  **synergy_basic_cert.pem** - SSL/TLS certificate
2.  **synergy_basic_key.pem** - SSL/TLS private key

## Script Metadata

The manifest shows:
- **Bytes**: Compressed size
- **LengthCol**: Decompressed size (in some encoding)
- **IsResource**: 0 for scripts, 1 for resource files

## Analysis Notes

- The driver uses an object-oriented architecture with interfaces
- Communication is handled through a priority queue system
- Supports both individual motors and groups
- Uses HTTPS/TLS for secure communication (hence the certificates)
- Written by Control Concepts, Inc. (see copyright in Polyfill.js)

## Tools for Extraction

### Python Script Example

```python
import olefile
import zlib
import os

def extract_driver(driver_path, output_dir):
    ole = olefile.OleFileIO(driver_path)

    for stream in ole.listdir():
        stream_path = '/'.join(stream)
        data = ole.openstream(stream).read()

        # Try to decompress with zlib
        try:
            decompressed = zlib.decompress(data)
            ext = '.js' if b'function' in decompressed or b'var' in decompressed else '.txt'
        except:
            decompressed = data
            ext = '.bin'

        # Write to file
        filename = os.path.join(output_dir, stream_path.replace('/', '_') + ext)
        with open(filename, 'wb') as f:
            f.write(decompressed)
```

## Security Considerations

The driver contains:
- **Unencrypted JavaScript source code** (after decompression)
- **SSL/TLS credentials** embedded in the driver
- No obfuscation beyond compression
- Standard driver architecture

The extraction reveals the complete driver implementation including protocol details, API endpoints, and communication methods used to control Somfy PoE motors.
