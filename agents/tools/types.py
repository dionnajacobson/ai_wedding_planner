"""Provider-neutral tool types shared by local handlers and LLM adapters."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    """Normalized tool schema independent of any LLM provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    params_model: type[BaseModel]


class ToolCall(BaseModel):
    """A tool invocation requested by an LLM."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Text output returned for one tool call."""

    tool_call_id: str
    content: str
