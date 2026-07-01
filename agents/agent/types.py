"""Agent configuration and result types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agents.client.types import Model
from agents.prompts.base import JinjaPrompt
from agents.tools.mcp.config import McpServer
from agents.tools.types import ToolDefinition, ToolResult


class Agent(BaseModel):
    """Configuration for a single LLM agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    model: Model
    prompt: JinjaPrompt
    tools: list[ToolDefinition | Agent | McpServer] = Field(default_factory=list)
    max_tool_rounds: int = Field(default=10, ge=1)
    max_tokens: int = Field(default=1024, ge=1)
    agent_description: str | None = None


class ToolEntry(BaseModel):
    """One tool exposed to the LLM, with an optional sub-agent to run on invocation."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    agent: Agent | None = None
    definition: ToolDefinition


class AgentRunResult(BaseModel):
    """Output from one agent run."""

    content: str
    tool_rounds: int = 0
    tool_results: list[ToolResult] = Field(default_factory=list)
