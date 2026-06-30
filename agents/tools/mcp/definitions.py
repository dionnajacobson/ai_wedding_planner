"""MCP tool definitions discovered from connected servers."""

from __future__ import annotations

from pydantic import Field

from agents.tools.types import ToolDefinition, ToolName, format_mcp_tool_name


class McpToolDefinition(ToolDefinition):
    """Schema-only tool definition discovered from an MCP server."""

    mcp_server_name: str
    mcp_tool_name: str
    name: ToolName = ToolName.MCP
    params_model: None = Field(default=None, exclude=True)

    @property
    def name_formatted(self) -> str:
        """Return the provider-facing MCP tool name."""
        formatted = format_mcp_tool_name(self.mcp_server_name, self.mcp_tool_name)
        return formatted
