"""Unit tests for MCP server configuration types."""

from __future__ import annotations

import pytest

from agents.tools.mcp.client_manager import McpClientManager
from agents.tools.mcp.config import ServerConfig, StdioConfig, StreamableHttpConfig


class TestServerConfig:
    """Table-driven tests for MCP server configuration."""

    def test_server_config_supports_streamable_http(self) -> None:
        """Accept streamable HTTP MCP server settings."""
        server = ServerConfig(
            config=StreamableHttpConfig(
                headers={"Authorization": "Bearer token"},
                url="https://example.com/mcp",
            ),
            name="remote",
            type="streamable_http",
        )
        assert server.config.url == "https://example.com/mcp"

    def test_server_config_validates_transport(self) -> None:
        """Reject MCP servers that omit required transport fields."""
        with pytest.raises(ValueError, match="stdio config"):
            ServerConfig(
                config=StreamableHttpConfig(url="https://example.com/mcp"),
                name="broken",
                type="stdio",
            )

    def test_resolve_servers_returns_explicit_servers(self) -> None:
        """Return MCP servers passed directly on an agent tool list."""
        configured = ServerConfig(
            config=StdioConfig(command="npx"),
            name="filesystem",
            type="stdio",
        )
        client = McpClientManager()

        resolved = client.resolve_servers([configured])

        assert resolved == (configured,)

    def test_agent_accepts_mcp_server_in_tools(self) -> None:
        """Allow fully configured MCP servers in agent tool lists."""
        from agents.agent.types import Agent
        from agents.client.types import Model
        from agents.prompts.base import JinjaPrompt

        class _Prompt(JinjaPrompt):
            template_name = "base.jinja"

        apify_server = ServerConfig(
            config=StreamableHttpConfig(url="https://mcp.apify.com"),
            name="apify",
            type="streamable_http",
        )
        agent = Agent(
            model=Model.GPT_4O_MINI_2024_07_18,
            name="vendor_search",
            prompt=_Prompt(),
            tools=[apify_server],
        )

        assert agent.tools[0].name == "apify"
