"""Local tool registry and execution router."""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from agents.tools.types import ToolCall, ToolDefinition, ToolResult

ToolHandler = Callable[[BaseModel], str]


class ToolRegistry:
    """Register local tools and execute tool calls by name."""

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        """Register one tool definition and its handler."""
        self._definitions[definition.name] = definition
        self._handlers[definition.name] = handler

    def definitions(self) -> list[ToolDefinition]:
        """Return all registered tool definitions."""
        definitions = list(self._definitions.values())
        return definitions

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Run one tool call and return its text result."""
        definition = self._definitions.get(tool_call.name)
        handler = self._handlers.get(tool_call.name)
        if definition is None or handler is None:
            raise ValueError(f"Unknown tool: {tool_call.name}")

        params = definition.params_model.model_validate(tool_call.arguments)
        content = handler(params)
        result = ToolResult(tool_call_id=tool_call.id, content=content)
        return result

    def execute_all(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Run multiple tool calls."""
        results = [self.execute(tool_call) for tool_call in tool_calls]
        return results
