"""Protocols for local tool executors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from agents.tools.types import ToolCall, ToolResult

if TYPE_CHECKING:
    from agents.agent.types import ToolEntry


@runtime_checkable
class ToolExecutor(Protocol):
    """Execute tool calls routed from the LLM by name.

    `tool_entry` (built by `prepare()`) carries `.agent` (the child to run,
    for agent-as-tool calls) and `.definition` (whose subclass may carry
    request-scoped values, e.g. `SaveVendorDefinition.session_id`).
    """

    async def execute(
        self,
        tool_call: ToolCall,
        tool_entry: ToolEntry,
        runner: Any,
    ) -> ToolResult:
        """Run one tool call and return its text result."""
        ...
