"""Unit tests for the tool orchestrator."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

from agents.agent import Agent, AgentToolInput
from agents.client.types import Model
from agents.prompts.base import JinjaPrompt
from agents.tools.agent_tool import AgentToolDefinition
from agents.tools.mcp.client_manager import McpClientManager
from agents.tools.mcp.config import McpServer
from agents.tools.mcp.definitions import McpToolDefinition
from agents.tools.mcp.tool import McpToolExecutor
from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.types import ToolCall, ToolName, format_agent_name
from tests.agents.mock_data import DaysUntilDateDefinition, DaysUntilDateExecutor


class _TaskPrompt(JinjaPrompt):
    template_name = "base.jinja"


class TestToolOrchestrator:
    """Table-driven tests for ToolOrchestrator."""

    def test_agent_to_tool_definition(self) -> None:
        """Run agent-as-tool definition scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "uses_agent_as_tool_name_and_description",
                "agent_kwargs": {
                    "name": "Researcher",
                    "agent_description": "Run the Researcher agent.",
                },
                "expected_description": "Run the Researcher agent.",
            },
            {
                "name": "defaults_description_from_agent_name",
                "agent_kwargs": {
                    "name": "Researcher",
                },
                "expected_description": "Run the Researcher agent.",
            },
        ]

        orchestrator = ToolOrchestrator()

        for case in test_cases:
            agent = Agent(
                model=Model.GPT_4O_MINI_2024_07_18,
                prompt=_TaskPrompt(),
                **case["agent_kwargs"],
            )
            tool_name = f"agent_as_tool_{format_agent_name(agent.name)}"
            definition = orchestrator._agent_to_tool_definition(agent)

            assert isinstance(definition, AgentToolDefinition)
            assert definition.name == ToolName.AGENT_AS_TOOL
            assert definition.description == case["expected_description"]
            assert definition.params_model is AgentToolInput
            assert definition.agent_name == format_agent_name(agent.name)
            assert definition.name_formatted == tool_name

    def test_execute(self) -> None:
        """Run execute scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "executes_days_until_date",
                "executor": DaysUntilDateExecutor(),
                "tool_call": ToolCall(
                    id="call_1",
                    name="days_until_date",
                    arguments={"event_date": "2099-01-01"},
                ),
                "expected_tool_call_id": "call_1",
                "content_is_digit": True,
            },
        ]

        for case in test_cases:
            # ARRANGE
            orchestrator = ToolOrchestrator(
                executors={ToolName.DAYS_UNTIL_DATE: case["executor"]},
            )

            # ACT
            result = asyncio.run(orchestrator.execute(case["tool_call"]))

            # ASSERT
            assert result.tool_call_id == case["expected_tool_call_id"]
            if case["content_is_digit"]:
                assert result.content.isdigit()

    def test_prepare_includes_configured_mcp_servers(self) -> None:
        """Configured MCP servers are merged during prepare without agent wiring."""
        server = McpServer(
            command="npx",
            name="filesystem",
        )
        definition = McpToolDefinition(
            description="Read a file",
            mcp_server_name="filesystem",
            mcp_tool_name="read_file",
            params_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        )
        client = AsyncMock(spec=McpClientManager)
        client.connect_server.return_value = [definition]
        client.servers_for_agent.return_value = (server,)
        orchestrator = ToolOrchestrator(
            executors={ToolName.MCP: McpToolExecutor(client=client)},
            mcp_client=client,
        )
        agent = Agent(
            mcp_servers=["filesystem"],
            model=Model.GPT_4O_MINI_2024_07_18,
            name="test",
            prompt=_TaskPrompt(),
            tools=[DaysUntilDateDefinition()],
        )

        entries = asyncio.run(orchestrator.prepare(agent))

        assert len(entries) == 2
        assert entries[0].definition.name_formatted == "mcp_filesystem_read_file"
        assert entries[1].definition.name == ToolName.DAYS_UNTIL_DATE
        client.connect_server.assert_awaited_once_with(server)

    def test_prepare(self) -> None:
        """Run prepare scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "wraps_tool_definitions",
                "tools": [DaysUntilDateDefinition()],
                "expected_entry_count": 1,
                "expected_agent_count": 0,
                "expected_tool_name": ToolName.DAYS_UNTIL_DATE,
            },
            {
                "name": "wraps_sub_agents",
                "tools": [
                    Agent(
                        name="Researcher",
                        model=Model.GPT_4O_MINI_2024_07_18,
                        prompt=_TaskPrompt(),
                    ),
                ],
                "expected_entry_count": 1,
                "expected_agent_count": 1,
                "expected_tool_name": ToolName.AGENT_AS_TOOL,
            },
        ]

        orchestrator = ToolOrchestrator()

        for case in test_cases:
            agent = Agent(
                model=Model.GPT_4O_MINI_2024_07_18,
                name="test",
                prompt=_TaskPrompt(),
                tools=case["tools"],
            )
            entries = asyncio.run(orchestrator.prepare(agent))

            assert len(entries) == case["expected_entry_count"]
            assert sum(entry.agent is not None for entry in entries) == case["expected_agent_count"]
            assert entries[0].definition.name == case["expected_tool_name"]
