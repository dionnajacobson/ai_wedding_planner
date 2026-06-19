import uuid

from pydantic import BaseModel, Field

from services.types import Message


class StartChatRequest(BaseModel):
    """Optional client details used when creating a new chat session."""

    first_name: str = Field(default="Guest", examples=["Alex"])
    last_name: str = Field(default="User", examples=["Smith"])
    email: str = Field(default="unknown@example.com", examples=["alex@example.com"])


class StartChatResponse(BaseModel):
    """Identifier for a newly created chat session."""

    session_id: uuid.UUID


class ChatRequest(BaseModel):
    """User message sent to the wedding planning assistant."""

    session_id: uuid.UUID
    message: str = Field(min_length=1, examples=["What should we book first?"])
    max_tokens: int = 1024


class ChatResponse(BaseModel):
    """Assistant reply for a chat turn."""

    session_id: uuid.UUID
    message: Message


class MessagesResponse(BaseModel):
    """Full conversation history for a session."""

    session_id: uuid.UUID
    messages: list[Message]
