# src/tests/test_send_message.py

import socket
import struct


def simulate_client():
    try:
        # Create socket and connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 5000))
        print("Connected to server successfully")

        # Get sender ID from user input
        print("Enter sender client ID (hex string format):")
        sender_id_string = input().strip()
        sender_id = bytes.fromhex(sender_id_string)
        if len(sender_id) != 16:
            print(f"Invalid ID length: got {len(sender_id)} bytes, expected 16")

        # Get destination ID from user input
        print("Enter destination client ID (hex string format):")
        dest_id_string = input().strip()
        dest_id = bytes.fromhex(dest_id_string)
        if len(dest_id) != 16:
            print(f"Invalid ID length: got {len(dest_id)} bytes, expected 16")

        # Get message type from user
        print("\nSelect message type:")
        print("1) Request for symmetric key")
        print("2) Send symmetric key")
        print("3) Send text message")
        message_type = int(input("Enter message type (1-3): "))

        if not 1 <= message_type <= 3:
            raise ValueError("Invalid message type. Must be between 1-4.")

        # Create send message request
        request = bytearray()

        # Add sender client ID
        request.extend(sender_id)
        print(f"Using sender ID: {sender_id.hex()}")

        # Version (1 byte)
        request.append(1)
        # Request code 603 for send message (2 bytes, little endian)
        request.extend((603).to_bytes(2, 'little'))

        # Create payload
        payload = bytearray()

        # Destination client ID (16 bytes)
        payload.extend(dest_id)
        print(f"Sending to destination ID: {dest_id.hex()}")

        # Message type
        payload.append(message_type)

        # Message content
        content = f"test message From: {sender_id.hex()}".encode('ascii')

        # Content size (4 bytes, little endian)
        payload.extend(len(content).to_bytes(4, 'little'))

        # Content
        payload.extend(content)

        # Add payload size to request header (4 bytes, little endian)
        request.extend(len(payload).to_bytes(4, 'little'))

        # Add the payload
        request.extend(payload)

        print(f"\nSending request: {len(request)} bytes")
        print(f"Message type: {message_type}")
        print(f"Content size: {len(content)} bytes")
        print(f"Content: {content.decode('ascii')}")

        # Send request
        client.send(request)

        # Get response
        response = client.recv(7)  # Version(1) + Code(2) + Size(4)
        if len(response) < 7:
            raise ValueError(f"Incomplete response header: got {len(response)} bytes instead of 7")

        version, code, payload_size = struct.unpack('<BHI', response)
        print(f"\nGot response: version={version}, code={code}, payload size={payload_size}")

        if code == 2103:  # Success response
            # Get payload (20 bytes: 16 for client ID + 4 for message ID)
            payload = client.recv(payload_size)
            if len(payload) != 20:
                raise ValueError(f"Incomplete payload: got {len(payload)} bytes instead of 20")

            dest_id = payload[:16]
            message_id = struct.unpack('<I', payload[16:])[0]

            print("\nMessage sent successfully:")
            print(f"Destination ID: {dest_id.hex()}")
            print(f"Message ID: {message_id}")

        elif code == 9000:  # Error response
            print("Server returned error - destination client probably doesn't exist")

        else:
            print(f"Unexpected response code: {code}")

    except Exception as e:
        print(f"Error: {e}")
        raise  # Re-raise to see full traceback
    finally:
        client.close()
        print("\nConnection closed")


if __name__ == "__main__":
    simulate_client()