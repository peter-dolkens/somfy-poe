"""Somfy PoE Motor Controller."""
import asyncio
import json
import logging
import socket
import ssl
from typing import Optional, Dict, Any

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from .const import TCP_PORT, UDP_PORT

_LOGGER = logging.getLogger(__name__)


class SomfyPoEMotorController:
    """Controller for a Somfy PoE motor."""

    def __init__(self, host: str, pin: str):
        """
        Initialize the motor controller.

        Args:
            host: IP address or hostname of the motor
            pin: 4-digit PIN code from motor label
        """
        self.host = host
        self.pin = pin
        self.target_id: Optional[str] = None
        self.aes_key: Optional[bytes] = None
        self.message_id = 1
        self._tcp_socket: Optional[ssl.SSLSocket] = None
        self._udp_socket: Optional[socket.socket] = None
        self._is_connected = False
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Return True if connected and authenticated."""
        return self._is_connected and self.aes_key is not None

    async def connect(self) -> bool:
        """
        Connect and authenticate with the motor.

        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            try:
                # Step 1: TCP connection with TLS
                await self._connect_tcp()

                # Step 2: Authenticate with PIN
                if not await self._authenticate():
                    return False

                # Step 3: Get AES encryption key
                if not await self._authorize():
                    return False

                # Step 4: Setup UDP socket
                await self._setup_udp()

                self._is_connected = True
                _LOGGER.info("Successfully connected to motor at %s", self.host)
                return True

            except Exception as err:
                _LOGGER.exception("Failed to connect to motor: %s", err)
                await self.disconnect()
                return False

    async def disconnect(self) -> None:
        """Disconnect from the motor."""
        async with self._lock:
            if self._tcp_socket:
                try:
                    self._tcp_socket.close()
                except Exception:
                    pass
                self._tcp_socket = None

            if self._udp_socket:
                try:
                    self._udp_socket.close()
                except Exception:
                    pass
                self._udp_socket = None

            self._is_connected = False
            _LOGGER.debug("Disconnected from motor")

    async def _connect_tcp(self) -> None:
        """Establish TCP connection with TLS."""
        loop = asyncio.get_event_loop()

        def _connect():
            # Create SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Create and wrap socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            ssl_sock = context.wrap_socket(sock, server_hostname=self.host)
            ssl_sock.connect((self.host, TCP_PORT))
            return ssl_sock

        self._tcp_socket = await loop.run_in_executor(None, _connect)
        _LOGGER.debug("TCP connection established to %s:%d", self.host, TCP_PORT)

    async def _send_tcp(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message over TCP and receive response."""
        if not self._tcp_socket:
            raise ConnectionError("Not connected")

        loop = asyncio.get_event_loop()

        def _send_receive():
            data = json.dumps(message)
            self._tcp_socket.sendall(data.encode("utf-8"))
            response_data = self._tcp_socket.recv(4096)
            return json.loads(response_data.decode("utf-8"))

        return await loop.run_in_executor(None, _send_receive)

    async def _authenticate(self) -> bool:
        """Authenticate with PIN code."""
        message = {
            "id": self.message_id,
            "method": "security.auth",
            "params": {"code": self.pin},
        }
        self.message_id += 1

        response = await self._send_tcp(message)

        if response.get("result"):
            self.target_id = response.get("targetID")
            _LOGGER.info("Authenticated successfully. Target ID: %s", self.target_id)
            return True

        _LOGGER.error("Authentication failed")
        return False

    async def _authorize(self) -> bool:
        """Get AES encryption key."""
        message = {"id": self.message_id, "method": "security.get"}
        self.message_id += 1

        response = await self._send_tcp(message)

        if response.get("result") and "key" in response:
            key_bytes = response["key"]
            self.aes_key = bytes(key_bytes)
            _LOGGER.info("Authorization successful. Key length: %d", len(self.aes_key))
            return True

        _LOGGER.error("Authorization failed")
        return False

    async def _setup_udp(self) -> None:
        """Setup UDP socket for motor commands."""
        loop = asyncio.get_event_loop()

        def _create_socket():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            return sock

        self._udp_socket = await loop.run_in_executor(None, _create_socket)
        _LOGGER.debug("UDP socket created")

    def _encrypt_message(self, message: str) -> bytes:
        """
        Encrypt message with AES-128-CBC.

        Args:
            message: JSON string to encrypt

        Returns:
            IV + encrypted data
        """
        # Generate random IV
        iv = get_random_bytes(16)

        # Create cipher
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)

        # Pad and encrypt
        message_bytes = message.encode("utf-8")
        padded_message = pad(message_bytes, AES.block_size)
        encrypted = cipher.encrypt(padded_message)

        # Return IV + encrypted data
        return iv + encrypted

    def _decrypt_message(self, data: bytes) -> str:
        """
        Decrypt AES-128-CBC message.

        Args:
            data: IV + encrypted data

        Returns:
            Decrypted JSON string
        """
        # Extract IV and encrypted data
        iv = data[:16]
        encrypted = data[16:]

        # Create cipher and decrypt
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted)

        # Remove padding
        message = unpad(decrypted, AES.block_size)

        return message.decode("utf-8")

    async def _send_udp(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send encrypted UDP message and receive response."""
        if not self._udp_socket or not self.aes_key:
            raise ConnectionError("Not connected or not authorized")

        loop = asyncio.get_event_loop()

        def _send_receive():
            # Encrypt and send
            data = json.dumps(message)
            encrypted = self._encrypt_message(data)
            self._udp_socket.sendto(encrypted, (self.host, UDP_PORT))

            # Receive and decrypt
            response_data, _ = self._udp_socket.recvfrom(4096)
            decrypted = self._decrypt_message(response_data)
            return json.loads(decrypted)

        return await loop.run_in_executor(None, _send_receive)

    async def move_up(self) -> bool:
        """Move motor to upper limit (open)."""
        if not self.is_connected:
            return False

        message = {
            "id": self.message_id,
            "method": "move.up",
            "params": {"targetID": self.target_id, "seq": 1},
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            return response.get("result", False)
        except Exception as err:
            _LOGGER.error("Failed to move up: %s", err)
            return False

    async def move_down(self) -> bool:
        """Move motor to lower limit (closed)."""
        if not self.is_connected:
            return False

        message = {
            "id": self.message_id,
            "method": "move.down",
            "params": {"targetID": self.target_id, "seq": 1},
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            return response.get("result", False)
        except Exception as err:
            _LOGGER.error("Failed to move down: %s", err)
            return False

    async def stop(self) -> bool:
        """Stop motor movement."""
        if not self.is_connected:
            return False

        message = {
            "id": self.message_id,
            "method": "move.stop",
            "params": {"targetID": self.target_id, "seq": 1},
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            return response.get("result", False)
        except Exception as err:
            _LOGGER.error("Failed to stop: %s", err)
            return False

    async def move_to_position(self, position: float) -> bool:
        """
        Move motor to specific position.

        Args:
            position: Position 0-100 (0=open, 100=closed)

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        message = {
            "id": self.message_id,
            "method": "move.to",
            "params": {
                "targetID": self.target_id,
                "position": float(position),
                "seq": 1,
            },
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            return response.get("result", False)
        except Exception as err:
            _LOGGER.error("Failed to move to position: %s", err)
            return False

    async def get_position(self) -> Optional[Dict[str, Any]]:
        """
        Get current motor position and status.

        Returns:
            Dictionary with position, direction, and status
        """
        if not self.is_connected:
            return None

        message = {
            "id": self.message_id,
            "method": "status.position",
            "params": {"targetID": self.target_id},
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            if response.get("result"):
                return response.get("position")
            return None
        except Exception as err:
            _LOGGER.error("Failed to get position: %s", err)
            return None

    async def get_info(self) -> Optional[Dict[str, Any]]:
        """
        Get motor information.

        Returns:
            Dictionary with motor info (name, model, firmware, etc.)
        """
        if not self.is_connected:
            return None

        message = {
            "id": self.message_id,
            "method": "status.info",
            "params": {"targetID": self.target_id},
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            if response.get("result"):
                return response.get("info")
            return None
        except Exception as err:
            _LOGGER.error("Failed to get info: %s", err)
            return None

    async def wink(self) -> bool:
        """Make motor jog briefly to identify it."""
        if not self.is_connected:
            return False

        message = {
            "id": self.message_id,
            "method": "move.wink",
            "params": {"targetID": self.target_id, "seq": 1},
        }
        self.message_id += 1

        try:
            response = await self._send_udp(message)
            return response.get("result", False)
        except Exception as err:
            _LOGGER.error("Failed to wink: %s", err)
            return False
