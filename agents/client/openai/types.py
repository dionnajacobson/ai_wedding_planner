"""OpenAI-specific request and response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OpenAIPayload(BaseModel):
    """
    Request payload for responses.create().
    https://developers.openai.com/api/reference/python/resources/responses/methods/create
    """

    input: str
    instructions: str
    model: str
    max_output_tokens: int
    tools: list[dict[str, Any]] | None = None
