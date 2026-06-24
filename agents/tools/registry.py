"""Local tool registry and execution router."""

from __future__ import annotations

import asyncio
import logging
import time

from agents.tools.protocols import Tool
from agents.tools.types import ToolCall, ToolDefinition, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Register local tools and execute tool calls by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register one tool implementation."""
        definition = tool.definition()
        self._tools[definition.name] = tool

    def definitions(self) -> list[ToolDefinition]:
        """Return all registered tool definitions."""
        definitions = [tool.definition() for tool in self._tools.values()]
        return definitions

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Run one tool call and return its text result."""
        tool = self._tools.get(tool_call.name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_call.name}")

        start = time.perf_counter()
        try:
            result = await tool.execute(tool_call)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "tool_execute_failed",
                extra={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.id,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "tool_execute_completed",
            extra={
                "tool_name": tool_call.name,
                "tool_call_id": tool_call.id,
                "duration_ms": duration_ms,
            },
        )
        return result

    async def execute_all(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Run multiple tool calls concurrently."""
        tasks = [self.execute(tool_call) for tool_call in tool_calls]
        results = await asyncio.gather(*tasks)
        return list(results)
