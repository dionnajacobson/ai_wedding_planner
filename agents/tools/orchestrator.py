"""Route and execute tool calls."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from agents.tools.agent_tool import AgentToolExecutor
from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolName, ToolResult
from agents.tools.web_search import WebSearchExecutor

if TYPE_CHECKING:
    from agents.agent.types import Agent

logger = logging.getLogger(__name__)


class ToolOrchestrator:
    """Execute tool calls and aggregate results."""

    def __init__(self, executors: dict[ToolName, ToolExecutor] | None = None) -> None:
        """Initialize with a tool-name to executor mapping."""
        self._executors = executors or {}

    @staticmethod
    def default() -> ToolOrchestrator:
        """Return an orchestrator with the standard executor set."""
        executors = {
            ToolName.WEB_SEARCH: WebSearchExecutor(),
            ToolName.AGENT_AS_TOOL: AgentToolExecutor(),
        }
        orchestrator = ToolOrchestrator(executors)
        return orchestrator

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agents: dict[str, Agent] | None = None,
        runner: Any | None = None,
    ) -> ToolResult:
        """Run one tool call and return its text result."""
        executor = self._get_executor(ToolName(tool_call.name))

        start = time.perf_counter()
        try:
            result = await executor.execute(tool_call, agents=agents, runner=runner)
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

    async def execute_all(
        self,
        tool_calls: list[ToolCall],
        *,
        agents: dict[str, Agent] | None = None,
        runner: Any | None = None,
    ) -> list[ToolResult]:
        """Run multiple tool calls concurrently."""
        tasks = [
            self.execute(tool_call, agents=agents, runner=runner) for tool_call in tool_calls
        ]
        results = await asyncio.gather(*tasks)
        return list(results)

    def _get_executor(self, tool_name: ToolName) -> ToolExecutor:
        """Get the executor for a tool name."""
        executor = self._executors.get(tool_name)
        if executor is None:
            raise ValueError(f"Unknown tool: {tool_name.value}")
        return executor
