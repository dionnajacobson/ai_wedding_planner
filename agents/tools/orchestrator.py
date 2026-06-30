"""Route and execute tool calls."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from agents.agent.types import Agent, ToolEntry
from agents.tools.agent_tool import AgentToolDefinition, AgentToolExecutor, AgentToolInput
from agents.tools.days_until_date import DaysUntilDateExecutor
from agents.tools.mcp.client_manager import McpClientManager
from agents.tools.mcp.config import McpServer
from agents.tools.mcp.tool import McpToolExecutor
from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolDefinition, ToolName, ToolResult, format_agent_name
from agents.tools.web_search import WebSearchExecutor

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
            ToolName.WEB_SEARCH: WebSearchExecutor(),
        }
        orchestrator = ToolOrchestrator(executors=executors, mcp_client=mcp_client)
        return orchestrator

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agent: Agent | None = None,
        runner: Any | None = None,
    ) -> ToolResult:
        """Run one tool call and return its text result."""
        if agent is not None:
            executor = self._get_executor(ToolName.AGENT_AS_TOOL)
        elif self._is_mcp_tool_name(tool_call.name):
            executor = self._get_executor(ToolName.MCP)
        else:
            tool_name = ToolName(tool_call.name)
            executor = self._get_executor(tool_name)

        start = time.perf_counter()
        try:
            result = await executor.execute(tool_call, agent=agent, runner=runner)
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
        entry_by_name = {}
        if entries is not None:
            entry_by_name = {entry.definition.name_formatted: entry for entry in entries}

        tasks = [
            self._execute_for_entry(tool_call, entry_by_name.get(tool_call.name), runner=runner)
            for tool_call in tool_calls
        ]
        results = await asyncio.gather(*tasks)
        result_list = list(results)
        return result_list

    async def prepare(self, tools: list[ToolDefinition | Agent | McpServer]) -> list[ToolEntry]:
        """Register tool definitions, MCP servers, and sub-agents for an agent run."""
        agent_servers = [tool for tool in tools if isinstance(tool, McpServer)]
        other_tools = [tool for tool in tools if not isinstance(tool, McpServer)]
        mcp_servers = self._mcp_client.servers_for_tools(agent_servers)

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

    async def _execute_for_entry(
        self,
        tool_call: ToolCall,
        entry: ToolEntry | None,
        *,
        runner: Any | None = None,
    ) -> ToolResult:
        """Route a provider-facing tool name through prepared entries when available."""
        agent = entry.agent if entry is not None else None
        result = await self.execute(tool_call, agent=agent, runner=runner)
        return result

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

    @staticmethod
    def _is_mcp_tool_name(name: str) -> bool:
        """Return whether a provider-facing name belongs to an MCP tool."""
        prefix = f"{ToolName.MCP.value}_"
        is_mcp = name.startswith(prefix)
        return is_mcp
