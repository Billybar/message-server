# src/tests/test_registration

import socket
import struct


def simulate_client():
    try:
        # Create socket and connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 5000))  # Using port - 5000
        print("Connected to server successfully")

        # Create registration request
        request = bytearray()
        # Client ID (16 bytes of zeros for registration)
        request.extend(b'\x00' * 16)
        # Version (1 byte)
        request.append(1)
        # Request code 600 for registration (2 bytes, little endian)
        request.extend((600).to_bytes(2, 'little'))

        # Create payload with proper padding
        username = "TestUser1"
        username_bytes = username.encode('ascii') + b'\x00'  # null terminated
        username_padded = username_bytes.ljust(255, b'\x00')  # Pad to exactly 255 bytes
        public_key = b'\x01' * 160  # Dummy public key
        payload = username_padded + public_key

        # Add payload size (4 bytes, little endian)
        request.extend(len(payload).to_bytes(4, 'little'))
        # Add the payload itself
        request.extend(payload)

        print(f"Sending registration request for user: {username}")
        client.send(request)

        # Get response
        response = client.recv(7)  # Version(1) + Code(2) + Size(4)
        version, code, size = struct.unpack('<BHI', response)
        print(f"Got response: version={version}, code={code}, payload size={size}")

        if size > 0:
            # Get client ID
            client_id = client.recv(size)
            print(f"Received client ID: {client_id.hex()}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("Connection closed")


if __name__ == "__main__":
    simulate_client()