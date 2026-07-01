"""Route and execute tool calls."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from agents.agent.types import Agent, ToolEntry
from agents.tools.mcp.client_manager import McpClientManager
from agents.tools.mcp.config import McpServer
from agents.tools.mcp.tool import McpToolExecutor
from agents.tools.protocols import ToolExecutor
from agents.tools.tools.agent_tool import AgentToolDefinition, AgentToolExecutor, AgentToolInput
from agents.tools.tools.days_until_date import DaysUntilDateExecutor
from agents.tools.tools.save_vendor import SaveVendorExecutor
from agents.tools.tools.web_search import WebSearchExecutor
from agents.tools.types import ToolCall, ToolName, ToolResult, format_agent_name

logger = logging.getLogger(__name__)


class ToolOrchestrator:
    """Execute tool calls and aggregate results."""

    def __init__(
        self,
        executors: dict[ToolName, ToolExecutor] | None = None,
        mcp_client: McpClientManager | None = None,
    ) -> None:
        """Initialize with a tool-name to executor mapping."""
        self._executors = executors or {}
        self._mcp_client = mcp_client or McpClientManager.default()

    @staticmethod
    def default() -> ToolOrchestrator:
        """Return an orchestrator with the standard executor set."""
        mcp_client = McpClientManager.default()
        executors = {
            ToolName.AGENT_AS_TOOL: AgentToolExecutor(),
            ToolName.DAYS_UNTIL_DATE: DaysUntilDateExecutor(),
            ToolName.MCP: McpToolExecutor(client=mcp_client),
            ToolName.SAVE_VENDOR: SaveVendorExecutor(),
            ToolName.WEB_SEARCH: WebSearchExecutor(),
        }
        orchestrator = ToolOrchestrator(executors=executors, mcp_client=mcp_client)
        return orchestrator

    async def execute(
        self,
        tool_call: ToolCall,
        tool_entry: ToolEntry,
        runner: Any,
    ) -> ToolResult:
        """Run one tool call and return its text result.

        `tool_entry` (built by `prepare()`) supplies the tool name and is
        passed whole to the executor, so a `ToolDefinition` subclass can carry
        whatever request-scoped values it needs (e.g.
        `SaveVendorDefinition.session_id`), since it's rebuilt fresh per call
        rather than shared like the executor.
        """
        tool_name = tool_entry.definition.name
        executor = self._get_executor(tool_name)

        start = time.perf_counter()
        try:
            result = await executor.execute(tool_call, tool_entry=tool_entry, runner=runner)
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
        entries: list[ToolEntry] | None = None,
        runner: Any | None = None,
    ) -> list[ToolResult]:
        """Run multiple tool calls concurrently."""
        entry_by_name = {entry.definition.provider_name: entry for entry in entries or []}

        tasks = []
        for tool_call in tool_calls:
            entry = entry_by_name.get(tool_call.name)
            if entry is None:
                raise ValueError(f"Unknown tool: {tool_call.name}")
            task = self.execute(tool_call, tool_entry=entry, runner=runner)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        result_list = list(results)
        return result_list

    async def prepare(self, agent: Agent) -> list[ToolEntry]:
        """Register tool definitions, MCP servers, and sub-agents for an agent run."""
        tool_servers = [tool for tool in agent.tools if isinstance(tool, McpServer)]
        other_tools = [tool for tool in agent.tools if not isinstance(tool, McpServer)]
        mcp_servers = self._mcp_client.resolve_servers(tool_servers)

        entries: list[ToolEntry] = []
        for server in mcp_servers:
            definitions = await self._mcp_client.connect_server(server)
            for definition in definitions:
                entry = ToolEntry(definition=definition)
                entries.append(entry)

        for tool in other_tools:
            if isinstance(tool, Agent):
                definition = self._agent_to_tool_definition(tool)
                entry = ToolEntry(agent=tool, definition=definition)
            else:
                entry = ToolEntry(definition=tool)
            entries.append(entry)
        return entries

    async def shutdown(self) -> None:
        """Close MCP sessions opened while preparing tool calls."""
        await self._mcp_client.shutdown()

    def _agent_to_tool_definition(self, agent: Agent) -> AgentToolDefinition:
        """Serialize an agent into a schema-only tool definition for a parent agent."""
        description = agent.agent_description or f"Run the {agent.name} agent."
        definition = AgentToolDefinition(
            agent_name=format_agent_name(agent.name),
            description=description,
            name=ToolName.AGENT_AS_TOOL,
            params_model=AgentToolInput,
        )
        return definition

    def _get_executor(self, tool_name: ToolName) -> ToolExecutor:
        """Get the executor for a tool name."""
        executor = self._executors.get(tool_name)
        if executor is None:
            raise ValueError(f"Unknown tool: {tool_name.value}")
        return executor
