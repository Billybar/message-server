# src/tests/test_clients_list.py

import socket
import struct


def simulate_client():
    try:
        # Create socket and connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 5000))
        print("Connected to server successfully")

        # Create request for clients list
        request = bytearray()
        # Dummy client ID (16 bytes - using all 1's for testing)
        client_id = b'\x01' * 16
        request.extend(client_id)
        print(f"Using client ID: {client_id.hex()}")

        # Version (1 byte)
        request.append(1)
        # Request code 601 for clients list (2 bytes, little endian)
        request.extend((601).to_bytes(2, 'little'))
        # Payload size - 0 for this request (4 bytes)
        request.extend((0).to_bytes(4, 'little'))

        print(f"Sending request of {len(request)} bytes: {request.hex()}")
        bytes_sent = client.send(request)
        print(f"Sent {bytes_sent} bytes")

        # Get response header
        response = bytearray()
        total_received = 0
        while total_received < 7:  # We expect 7 bytes for header
            chunk = client.recv(7 - total_received)
            if not chunk:
                raise ConnectionError("Connection closed by server")
            response.extend(chunk)
            total_received += len(chunk)
            print(f"Received chunk of {len(chunk)} bytes: {chunk.hex()}")

        if len(response) < 7:
            raise ValueError(f"Incomplete response header: got {len(response)} bytes instead of 7")

        version, code, payload_size = struct.unpack('<BHI', response)
        print(f"Got response: version={version}, code={code}, payload size={payload_size}")

        if payload_size > 0:
            # Get payload
            payload = bytearray()
            total_received = 0
            while total_received < payload_size:
                chunk = client.recv(min(4096, payload_size - total_received))
                if not chunk:
                    raise ConnectionError("Connection closed by server while receiving payload")
                payload.extend(chunk)
                total_received += len(chunk)
                print(f"Received payload chunk of {len(chunk)} bytes")

            # Calculate number of clients (each client entry is 16 + 255 bytes)
            num_clients = len(payload) // (16 + 255)
            print(f"\nReceived data for {num_clients} clients")

            # Parse each client's data
            for i in range(num_clients):
                start_idx = i * (16 + 255)
                client_id = payload[start_idx:start_idx + 16]
                username_bytes = payload[start_idx + 16:start_idx + 16 + 255]
                # Find null terminator in username
                username = username_bytes.split(b'\x00')[0].decode('ascii')

                print(f"\nClient {i + 1}:")
                print(f"ID: {client_id.hex()}")
                print(f"Username: {username}")

        else:
            print("No other clients registered")

    except Exception as e:
        print(f"Error: {e}")
        raise  # Re-raise to see full traceback
    finally:
        client.close()
        print("\nConnection closed")


if __name__ == "__main__":
    simulate_client()