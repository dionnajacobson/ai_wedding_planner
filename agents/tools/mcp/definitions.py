"""MCP tool definitions discovered from connected servers."""

from __future__ import annotations

from pydantic import Field

from agents.tools.types import ToolDefinition, ToolName, format_agent_name


class McpToolDefinition(ToolDefinition):
    """Schema-only tool definition discovered from an MCP server."""

    mcp_server_name: str
    mcp_tool_name: str
    name: ToolName = ToolName.MCP
    params_model: None = Field(default=None, exclude=True)

    @staticmethod
    def format_name(server_name: str, tool_name: str) -> str:
        """Build a provider-safe tool name for an MCP tool."""
        server_slug = format_agent_name(server_name)
        tool_slug = format_agent_name(tool_name)
        return f"{ToolName.MCP.value}_{server_slug}_{tool_slug}"

    @property
    def name_formatted(self) -> str:
        """Return the provider-facing MCP tool name."""
        return self.format_name(self.mcp_server_name, self.mcp_tool_name)
