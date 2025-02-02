# src/tests/test_pending_messages.py

import socket
import struct


def simulate_client():
    try:
        # Create socket and connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 5000))
        print("Connected to server successfully")

        # Get client ID from user input
        print("Enter client ID (hex string format):")
        client_id_hex = input().strip()

        # Convert hex string to bytes
        client_id = bytes.fromhex(client_id_hex)
        if len(client_id) != 16:
            raise ValueError(f"Invalid ID length: got {len(client_id)} bytes, expected 16")

        # Create request
        request = bytearray()

        # Client ID
        request.extend(client_id)
        print(f"Requesting messages for client ID: {client_id.hex()}")

        # Version
        request.append(1)

        # Code 604
        request.extend((604).to_bytes(2, 'little'))

        # Payload size (0 for this request)
        request.extend((0).to_bytes(4, 'little'))

        # Send request
        client.send(request)

        # Get response
        response = client.recv(7)  # Version(1) + Code(2) + Size(4)
        version, code, size = struct.unpack('<BHI', response)
        print(f"Got response: version={version}, code={code}, size={size}")

        if code == 2104:  # Success
            if size == 0:
                print("No pending messages")
            else:
                # Read payload
                payload = client.recv(size)
                offset = 0
                msg_count = 0

                # Parse messages
                while offset < len(payload):
                    # Get sender ID (16 bytes)
                    sender_id = payload[offset:offset + 16]
                    offset += 16

                    # Get message ID (4 bytes)
                    msg_id = struct.unpack('<I', payload[offset:offset + 4])[0]
                    offset += 4

                    # Get message type (1 byte)
                    msg_type = payload[offset]
                    offset += 1

                    # Get content size (4 bytes)
                    content_size = struct.unpack('<I', payload[offset:offset + 4])[0]
                    offset += 4

                    # Get content
                    content = None
                    if content_size > 0:
                        content = payload[offset:offset + content_size]
                        offset += content_size

                    msg_count += 1
                    print(f"\nMessage {msg_count}:")
                    print(f"From: {sender_id.hex()}")
                    print(f"Message ID: {msg_id}")
                    print(f"Type: {msg_type}")
                    if content:
                        try:
                            print(f"Content: {content.decode('ascii')}")
                        except UnicodeDecodeError:
                            print(f"Content (hex): {content.hex()}")

        elif code == 9000:
            print("Error response from server")

    except ValueError as e:
        print(f"Input error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        print("\nConnection closed")


if __name__ == "__main__":
    simulate_client()