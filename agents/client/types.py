"""Client-agnostic LLM request and response models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from agents.tools.types import ToolCall, ToolDefinition


class Model(Enum):
    """OpenAI models."""

    GPT_4O_MINI_2024_07_18 = "openai/gpt-4o-mini-2024-07-18"

    def provider_name(self) -> str:
        """Get the provider for the model."""
        provider = self.value.split("/")[0]
        return provider

    def model_name(self) -> str:
        """Get the model name for the model."""
        model_name = self.value.split("/")[1]
        return model_name


class LLMRequest(BaseModel):
    """Normalized input for any LLM provider."""

    system: str
    user: str
    model: Model
    tools: list[ToolDefinition] | None = None
    max_tokens: int = 1024


class LLMResponse(BaseModel):
    """Normalized output from any LLM provider."""

    content: str | None
    model: str
    tool_calls: list[ToolCall] | None = None
