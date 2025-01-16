# src/server/server.py

import socket
import threading
from typing import Dict, List
import uuid
import logging
import struct
from datetime import datetime

from server_config import ServerConfig
from user import User
from message import Message, MessageType

class MessageUServer:
    VERSION = 1

    def __init__(self):
        """Initialize the server"""
        self.port = ServerConfig.read_port()
        self.clients: Dict[bytes, User] = {}  # Map User ID to User object
        self.messages: List[Message] = []  # List of pending messages
        self.lock = threading.Lock()  # Lock for thread safety

    def start(self):
        """Start the server and listen for connections"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('127.0.0.1', self.port))
        server_socket.listen()

        logging.info(f"Server starting on port {self.port}")

        while True:
            try:
                client_socket, address = server_socket.accept()
                logging.info(f"New connection from {address}")

                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.start()

            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

    def handle_client(self, client_socket: socket.socket):
        try:
            # logging.info("Waiting to receive data...")
            header = client_socket.recv(23)
            logging.info(f"Received header data: {header}, length: {len(header)}")

            if not header:
                logging.error("No data received")
                return
            if len(header) < 23:
                logging.error(f"Incomplete header received: {len(header)} bytes instead of 23")
                return

            client_id = header[:16]
            version = header[16]
            code = struct.unpack('<H', header[17:19])[0]
            payload_size = struct.unpack('<I', header[19:23])[0]

            # Read payload if exists
            payload = b''
            if payload_size > 0:
                payload = client_socket.recv(payload_size)

            # Handle the request based on code
            if code == 600:
                self.handle_registration(client_socket, payload)
            elif code == 601:
                self.handle_clients_list(client_socket, client_id)
            elif code == 602:
                self.handle_public_key(client_socket, client_id, payload)
            elif code == 603:
                self.handle_send_message(client_socket, client_id, payload)
            elif code == 604:
                self.handle_pending_messages(client_socket, client_id)
            else:
                self.send_error(client_socket)

        except Exception as e:
            logging.error(f"Error handling client: {e}")
            self.send_error(client_socket)
        finally:
            client_socket.close()

    def handle_registration(self, client_socket: socket.socket, payload: bytes):
        """
        Handle client registration request

        Args:
            client_socket: The client's socket connection
            payload: Bytes containing username (255 bytes) and public key (160 bytes)
        """
        try:
            # Validate payload size
            if len(payload) != 415:  # 255 bytes username + 160 bytes public key
                raise ValueError(f"Invalid payload length: {len(payload)}")

            # Extract username (first 255 bytes) and find null terminator
            username_bytes = payload[:255]
            null_pos = username_bytes.find(b'\x00')

            if null_pos == -1:
                raise ValueError("No null terminator in username")

            # Get actual username by taking bytes up to null terminator
            username = username_bytes[:null_pos].decode('ascii')

            # Extract public key (last 160 bytes)
            public_key = payload[255:415]

            if len(public_key) != 160:
                raise ValueError(f"Invalid public key length: {len(public_key)}")

            # Check if username already exists
            with self.lock:
                for user in self.clients.values():
                    if user.username == username:
                        logging.warning(f"Registration failed - username already exists: {username}")
                        self.send_error(client_socket)
                        return

                # Generate new UUID for client
                client_id = uuid.uuid4().bytes

                # Create and store new user
                new_user = User(client_id, username, public_key)
                self.clients[client_id] = new_user

                # Send success response with client ID
                response = struct.pack('<BHI', self.VERSION, 2100, 16)  # Version, Code, Size
                response += client_id
                client_socket.send(response)

                logging.info(f"Registered new user: {username}")

        except Exception as e:
            logging.error(f"Registration error: {e}")
            self.send_error(client_socket)

    def handle_clients_list(self, client_socket: socket.socket, client_id: bytes):
        """
        Handle request for clients list (code 601)
        Returns list of all registered clients except the requesting client
        Each client entry contains ID (16 bytes) and username (255 bytes, null terminated)
        """
        try:
            with self.lock:
                # Create payload for each client except requesting client
                payload = bytearray()
                for user in self.clients.values():
                    if user.ID != client_id:  # Skip requesting client
                        # Add client ID (16 bytes)
                        payload.extend(user.ID)
                        # Add null terminated username padded to 255 bytes
                        username_bytes = user.username.encode('ascii') + b'\x00'
                        username_bytes = username_bytes.ljust(255, b'\x00')
                        payload.extend(username_bytes)

                # Send response
                response_header = struct.pack('<BHI', self.VERSION, 2101, len(payload))
                response = response_header + payload
                client_socket.send(response)

                logging.info(f"Sent client list, size: {len(payload)}")

        except Exception as e:
            logging.error(f"Error handling clients list request: {e}")
            self.send_error(client_socket)

    def handle_public_key(self, client_socket: socket.socket, client_id: bytes, payload: bytes):
        """
        Handle request for client's public key (code 602)

        Args:
            client_socket: The client's socket connection
            client_id: ID of requesting client (16 bytes)
            payload: Contains the client ID whose public key is being requested (16 bytes)
        """
        try:
            # Validate payload size - should contain exactly one client ID (16 bytes)
            if len(payload) != 16:
                raise ValueError(f"Invalid payload length: {len(payload)}")

            # Get requested client ID from payload
            requested_id = payload

            with self.lock:
                # Check if requested client exists
                if requested_id not in self.clients:
                    self.send_error(client_socket)
                    return

                # Get public key for requested client
                public_key = self.clients[requested_id].public_key

                # Send response with client ID and public key
                response_header = struct.pack('<BHI', self.VERSION, 2102, len(requested_id) + len(public_key))
                response = response_header + requested_id + public_key
                client_socket.send(response)

        except Exception as e:
            logging.error(f"Error handling public key request: {e}")
            self.send_error(client_socket)

    def handle_send_message(self, client_socket: socket.socket, client_id: bytes, payload: bytes):
        """Handle sending a message between clients"""
        # TODO: Implement message sending logic
        pass

    def handle_pending_messages(self, client_socket: socket.socket, client_id: bytes):
        """Handle request for pending messages"""
        # TODO: Implement pending messages logic
        pass

    def send_error(self, client_socket: socket.socket):
        """Send error response to client"""
        response = struct.pack('<BHI', self.VERSION, 9000, 0)
        client_socket.send(response)


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Start server
    server = MessageUServer()
    server.start()


if __name__ == "__main__":
    main()