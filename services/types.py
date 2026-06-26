from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel

from db.models import MessageRole


class Client(BaseModel):
    """User model."""

    email: str
    first_name: str
    id: uuid.UUID
    last_name: str
    wedding_id: uuid.UUID | None = None


class Wedding(BaseModel):
    """Wedding model."""

    budget: float | None = None
    client: Client
    id: uuid.UUID
    location: str | None = None
    session_ids: list[uuid.UUID]
    wedding_date: date | None = None


class Message(BaseModel):
    """Message model."""

    content: str
    id: uuid.UUID
    role: MessageRole
