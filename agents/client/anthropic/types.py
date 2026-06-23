"""Anthropic-specific request models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnthropicMessage(BaseModel):
    """Single message in an Anthropic messages request."""

    role: str
    content: str


class AnthropicPayload(BaseModel):
    """
    Request payload for messages.create().
    https://docs.anthropic.com/en/api/messages
    """

    model: str
    max_tokens: int
    system: str
    messages: list[AnthropicMessage]
    tools: list[dict[str, Any]] | None = None
