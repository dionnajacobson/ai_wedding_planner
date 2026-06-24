"""Protocols for local tool executors."""

from typing import Protocol, runtime_checkable

from agents.tools.types import ToolCall, ToolResult


@runtime_checkable
class ToolExecutor(Protocol):
    """Execute tool calls routed from the LLM by name."""

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Run one tool call and return its text result."""
        ...
