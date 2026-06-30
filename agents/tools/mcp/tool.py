"""MCP-backed tool executor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents.tools.mcp.client_manager import McpClientManager
from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolResult

if TYPE_CHECKING:
    from agents.agent.types import Agent


class McpToolExecutor(ToolExecutor):
    """Forward tool calls to a connected MCP server."""

    def __init__(self, client: McpClientManager | None = None) -> None:
        """Initialize with an optional MCP client for tests."""
        self._client = client or McpClientManager.default()

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agent: Agent | None = None,
        runner: Any | None = None,
    ) -> ToolResult:
        """Call the mapped MCP tool and return its text output."""
        content = await self._client.call_tool(tool_call.name, tool_call.arguments)
        result = ToolResult(content=content, tool_call_id=tool_call.id)
        return result
