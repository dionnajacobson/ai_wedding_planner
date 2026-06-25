"""Provider-neutral tool types shared by local handlers and LLM adapters."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def format_agent_name(name: str) -> str:
    """Normalize an agent name to lowercase snake_case for tool routing."""
    slug = re.sub(r"[\W_]+", "_", name.lower().strip())
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")


class ToolName(StrEnum):
    """Registered tool names."""

    AGENT_AS_TOOL = "agent_as_tool"
    DAYS_UNTIL_DATE = "days_until_date"
    WEB_SEARCH = "web_search"


class ToolDefinition(BaseModel):
    """Normalized tool schema independent of any LLM provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: ToolName
    description: str
    params_model: type[BaseModel]

    @property
    def name_formatted(self) -> str:
        """Return the provider-facing tool name."""
        return self.name.value


class AgentToolDefinition(ToolDefinition):
    """Schema-only tool definition for an agent exposed as a tool."""

    agent_name: str

    @property
    def name_formatted(self) -> str:
        """Return the provider-facing tool name."""
        return f"{self.name.value}_{self.agent_name}"


class ToolCall(BaseModel):
    """A tool invocation requested by an LLM."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    tool_key: str | None = None


class ToolResult(BaseModel):
    """Text output returned for one tool call."""

    tool_call_id: str
    content: str
