"""Provider-neutral tool types shared by local handlers and LLM adapters."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolName(str, Enum):
    """Registered tool names."""

    DAYS_UNTIL_DATE = "days_until_date"
    WEB_SEARCH = "web_search"


class ToolDefinition(BaseModel):
    """Normalized tool schema independent of any LLM provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: ToolName
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
