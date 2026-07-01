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

    @property
    def provider_name(self) -> str:
        """Return the provider-facing MCP tool name."""
        server_slug = format_agent_name(self.mcp_server_name)
        tool_slug = format_agent_name(self.mcp_tool_name)
        formatted_name = f"{ToolName.MCP.value}_{server_slug}_{tool_slug}"
        return formatted_name
