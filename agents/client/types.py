"""Client-agnostic LLM request and response models."""

from __future__ import annotations

from enum import Enum, StrEnum

from pydantic import BaseModel

from agents.tools.types import ToolCall, ToolDefinition


class Provider(StrEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Model(Enum):
    """LLM models keyed as provider/model-name."""

    GPT_4O_MINI_2024_07_18 = "openai/gpt-4o-mini-2024-07-18"
    CLAUDE_SONNET_4_6 = "anthropic/claude-sonnet-4-6"


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
    model: Model
    tool_calls: list[ToolCall] | None = None
