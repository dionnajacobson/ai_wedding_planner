"""Provider-neutral tool types shared by local handlers and LLM adapters."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def format_agent_name(name: str) -> str:
    """Normalize an agent name to lowercase snake_case for tool routing."""
    slug = re.sub(r"[\W_]+", "_", name.lower().strip())
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")


class ToolName(StrEnum):
    """Registered tool names."""

    AGENT_AS_TOOL = "agent_as_tool"
    DAYS_UNTIL_DATE = "days_until_date"
    MCP = "mcp"
    WEB_SEARCH = "web_search"


class ToolDefinition(BaseModel):
    """Normalized tool schema independent of any LLM provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    name: ToolName
    params_model: type[BaseModel] | None = None
    params_schema: dict[str, Any] | None = None

    @property
    def provider_name(self) -> str:
        """Return the provider-facing tool name."""
        return self.name.value

    @model_validator(mode="after")
    def validate_schema_source(self) -> ToolDefinition:
        """Require either a Pydantic model or a JSON schema."""
        if self.params_model is None and self.params_schema is None:
            raise ValueError("Either params_model or params_schema is required")
        return self


class ToolCall(BaseModel):
    """A tool invocation requested by an LLM."""

    arguments: dict[str, Any] = Field(default_factory=dict)
    id: str
    name: str


class ToolResult(BaseModel):
    """Text output returned for one tool call."""

    content: str
    tool_call_id: str
