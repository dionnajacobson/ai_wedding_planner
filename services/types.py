import uuid
from enum import Enum

from pydantic import BaseModel


class MessageRole(str, Enum):
    """Message role."""
    USER = "user"
    ASSISTANT = "assistant"


class Client(BaseModel):
    """User model."""

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    wedding_id: uuid.UUID | None = None


class Wedding(BaseModel):
    """Wedding model."""

    id: uuid.UUID
    client: Client
    session_ids: list[uuid.UUID]

class Message(BaseModel):
    """Message model."""

    id: uuid.UUID
    role: MessageRole
    content: str