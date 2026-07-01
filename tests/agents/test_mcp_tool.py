"""Unit tests for MCP-backed agent tools."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import mcp.types as mcp_types

from agents.agent import Agent
from agents.client.types import Model
from agents.prompts.prompts import VendorSearchPromptJinja
from agents.tools.mcp import McpClientManager, McpToolDefinition, McpToolExecutor
from agents.tools.mcp.config import ServerConfig, StdioConfig
from agents.tools.mcp.client_manager import McpClientManager as ClientManagerClass
from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.types import ToolCall, ToolName


class TestMcpToolNaming:
    """Table-driven tests for MCP tool name formatting."""

    def test_format_mcp_tool_name(self) -> None:
        """Run MCP tool name formatting scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "prefixes_server_and_tool",
                "server_name": "filesystem",
                "tool_name": "read_file",
                "expected": "mcp_filesystem_read_file",
            },
        ]

        for case in test_cases:
            formatted = McpToolDefinition.format_name(case["server_name"], case["tool_name"])
            assert formatted == case["expected"]


class TestMcpToolExecutor:
    """Table-driven tests for MCP tool execution."""

    def test_execute_delegates_to_client(self) -> None:
        """Run MCP execute scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_client_text",
                "arguments": {"path": "/tmp/plan.txt"},
                "expected_content": "file contents",
                "tool_name": "mcp_filesystem_read_file",
            },
        ]

        for case in test_cases:
            # ARRANGE
            client = AsyncMock(spec=McpClientManager)
            client.call_tool.return_value = case["expected_content"]
            executor = McpToolExecutor(client=client)
            tool_call = ToolCall(
                arguments=case["arguments"],
                id="call_1",
                name=case["tool_name"],
            )

            # ACT
            result = asyncio.run(executor.execute(tool_call))

            # ASSERT
            assert result.tool_call_id == "call_1"
            assert result.content == case["expected_content"]
            client.call_tool.assert_awaited_once_with(case["tool_name"], case["arguments"])


class TestMcpOrchestratorIntegration:
    """Table-driven tests for MCP server registration in the orchestrator."""

    def test_prepare_registers_mcp_tools(self) -> None:
        """Run MCP prepare scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "expands_mcp_server_into_tool_entries",
                "server": ServerConfig(
                    config=StdioConfig(
                        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                        command="npx",
                    ),
                    name="filesystem",
                    type="stdio",
                ),
                "expected_tool_name": "mcp_filesystem_read_file",
            },
        ]

        for case in test_cases:
            # ARRANGE
            definition = McpToolDefinition(
                description="Read a file",
                mcp_server_name="filesystem",
                mcp_tool_name="read_file",
                params_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            )
            client = AsyncMock(spec=McpClientManager)
            client.connect_server.return_value = [definition]
            client.resolve_servers.return_value = (case["server"],)
            orchestrator = ToolOrchestrator(
                executors={ToolName.MCP: McpToolExecutor(client=client)},
                mcp_client=client,
            )
            agent = Agent(
                model=Model.GPT_4O_MINI_2024_07_18,
                name="vendor_search",
                prompt=VendorSearchPromptJinja(query="Find florists", history=[]),
                tools=[case["server"]],
            )

            # ACT
            entries = asyncio.run(orchestrator.prepare(agent))

            # ASSERT
            assert len(entries) == 1
            assert entries[0].definition.name_formatted == case["expected_tool_name"]
            client.connect_server.assert_awaited_once_with(case["server"])

    def test_execute_routes_mcp_tool_names(self) -> None:
        """Run MCP execute routing scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "routes_prefixed_name_to_mcp_executor",
                "expected_content": "done",
                "tool_name": "mcp_filesystem_read_file",
            },
        ]

        for case in test_cases:
            # ARRANGE
            client = AsyncMock(spec=McpClientManager)
            client.call_tool.return_value = case["expected_content"]
            orchestrator = ToolOrchestrator(
                executors={ToolName.MCP: McpToolExecutor(client=client)},
                mcp_client=client,
            )
            tool_call = ToolCall(
                arguments={"path": "/tmp/plan.txt"},
                id="call_2",
                name=case["tool_name"],
            )

            # ACT
            result = asyncio.run(orchestrator.execute(tool_call))

            # ASSERT
            assert result.content == case["expected_content"]
            client.call_tool.assert_awaited_once_with(case["tool_name"], {"path": "/tmp/plan.txt"})


class TestMcpClientManagerFormatting:
    """Table-driven tests for MCP result formatting."""

    def test_format_call_tool_result(self) -> None:
        """Run MCP result formatting scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "joins_text_blocks",
                "result": mcp_types.CallToolResult(
                    content=[mcp_types.TextContent(type="text", text="hello")],
                ),
                "expected": "hello",
            },
            {
                "name": "prefixes_errors",
                "result": mcp_types.CallToolResult(
                    content=[mcp_types.TextContent(type="text", text="missing file")],
                    isError=True,
                ),
                "expected": "Error: missing file",
            },
        ]

        for case in test_cases:
            formatted = ClientManagerClass._format_call_tool_result(case["result"])
            assert formatted == case["expected"]
