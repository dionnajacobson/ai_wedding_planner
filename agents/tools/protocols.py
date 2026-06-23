"""Protocols for local tool implementations."""

from typing import Protocol, runtime_checkable

from agents.tools.types import ToolCall, ToolDefinition, ToolResult


@runtime_checkable
class Tool(Protocol):
    """A local tool that exposes schema to the LLM and executes tool calls."""

    def definition(self) -> ToolDefinition:
        """Return the normalized tool schema for LLM adapters."""
        ...

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Run one tool call and return its text result."""
        ...
