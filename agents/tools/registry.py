"""Local tool registry and execution router."""

from __future__ import annotations

import asyncio
import logging
import time

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolName, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Route LLM tool calls to registered executors by name."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._executors: dict[str, ToolExecutor] = {}

    @staticmethod
    def default() -> ToolRegistry:
        """Get the default tool registry."""
        from agents.tools.web_search import WebSearchExecutor

        tool_registry = ToolRegistry()
        tool_registry.register(ToolName.WEB_SEARCH, WebSearchExecutor())
        return tool_registry

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Run one tool call and return its text result."""
        executor = self._executors.get(tool_call.name)
        if executor is None:
            raise ValueError(f"Unknown tool: {tool_call.name}")

        start = time.perf_counter()
        try:
            result = await executor.execute(tool_call)
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

    def register(self, name: ToolName, executor: ToolExecutor) -> None:
        """Register one executor under a tool name."""
        self._executors[name.value] = executor
