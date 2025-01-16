# src/tests/test_public_key.py

import socket
import struct


def simulate_client():
    try:
        # Create socket and connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 5000))
        print("Connected to server successfully")

        # Get target ID from user input
        print("Enter the client ID you want to get public key for (hex string format):")
        target_id_string = input().strip()  # e.g. 7a7434d025cf46788e4368f735be3d65
        target_id = bytes.fromhex(target_id_string)

        if len(target_id) != 16:
            raise ValueError(f"Invalid ID length: got {len(target_id)} bytes, expected 16")

        # Create request for public key
        request = bytearray()

        # Dummy requesting client ID (16 bytes)
        requesting_id = b'\x01' * 16
        request.extend(requesting_id)

        # Version (1 byte)
        request.append(1)

        # Request code 602 for public key request (2 bytes, little endian)
        request.extend((602).to_bytes(2, 'little'))

        # Add payload size (4 bytes, little endian)
        request.extend(len(target_id).to_bytes(4, 'little'))

        # Add the payload (target client ID)
        request.extend(target_id)

        print(f"Requesting public key for target ID: {target_id.hex()}")

        # Send request
        print(f"Sending request of {len(request)} bytes: {request.hex()}")
        client.send(request)

        # Get response header
        response = client.recv(7)  # Version(1) + Code(2) + Size(4)
        if len(response) < 7:
            raise ValueError(f"Incomplete response header: got {len(response)} bytes instead of 7")

        version, code, payload_size = struct.unpack('<BHI', response)
        print(f"Got response: version={version}, code={code}, payload size={payload_size}")

        if code == 2102:  # Success response
            # Get payload
            payload = client.recv(payload_size)
            if len(payload) != payload_size:
                raise ValueError(f"Incomplete payload: got {len(payload)} bytes instead of {payload_size}")

            # Parse payload
            if payload_size == 176:  # 16 bytes client ID + 160 bytes public key
                client_id = payload[:16]
                public_key = payload[16:]

                print("\nReceived public key data:")
                print(f"Client ID: {client_id.hex()}")
                print(f"Public Key ({len(public_key)} bytes): {public_key.hex()}")
            else:
                print(f"Unexpected payload size: {payload_size}")

        elif code == 9000:  # Error response
            print("Server returned error - client probably doesn't exist")

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