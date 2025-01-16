from enum import IntEnum
from typing import Optional


class MessageType(IntEnum):
    """Enum for different message types"""
    REQUEST_FOR_SYMMETRIC_KEY = 1
    SEND_SYMMETRIC_KEY = 2
    SEND_TEXT_MESSAGE = 3
    SEND_FILE = 4  # Bonus feature


class Message:
    def __init__(self, ID: int, to_client: bytes, from_client: bytes,
                 msg_type: int, content: Optional[bytes] = None):
        """
        Initialize a new message
        Args:
            ID (int): 4 bytes message identifier
            to_client (bytes): 16 bytes (128 bit) recipient identifier
            from_client (bytes): 16 bytes (128 bit) sender identifier
            msg_type (int): 1 byte message type
            content (bytes, optional): Message content (encrypted)
        """
        if ID < 0 or ID > 0xFFFFFFFF:  # 4 bytes unsigned
            raise ValueError("ID must be a 4 byte unsigned integer")
        if len(to_client) != 16:
            raise ValueError("to_client must be 16 bytes")
        if len(from_client) != 16:
            raise ValueError("from_client must be 16 bytes")
        if msg_type not in MessageType.__members__.values():
            raise ValueError("Invalid message type")

        self.ID = ID
        self.to_client = to_client
        self.from_client = from_client
        self.type = msg_type
        self.content = content

    def __str__(self):
        """String representation of the message"""
        return (f"Message(ID={self.ID}, type={MessageType(self.type).name}, "
                f"content_size={len(self.content) if self.content else 0})")