"""Protocols for local tool executors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from agents.tools.types import ToolCall, ToolResult

if TYPE_CHECKING:
    from agents.agent.types import Agent


@runtime_checkable
class ToolExecutor(Protocol):
    """Execute tool calls routed from the LLM by name."""

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agent: Agent | None = None,
        runner: Any | None = None,
    ) -> ToolResult:
        """Run one tool call and return its text result."""
        ...
