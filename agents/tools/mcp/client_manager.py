"""MCP client session management for agent tool execution."""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any

import httpx
import mcp.types as mcp_types
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from agents.tools.mcp.config import McpServer, get_mcp_servers
from agents.tools.mcp.definitions import McpToolDefinition
from agents.tools.types import format_mcp_tool_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _McpToolRoute:
    """Route a provider-facing MCP tool name to a live session."""

    session: ClientSession
    tool_name: str


class McpClientManager:
    """Connect to MCP servers and expose their tools to the agent runtime."""

    def __init__(self, servers: tuple[McpServer, ...] | None = None) -> None:
        """Initialize an MCP client manager with optional server configuration."""
        self._exit_stack = AsyncExitStack()
        self._routes: dict[str, _McpToolRoute] = {}
        self._server_tools: dict[str, list[McpToolDefinition]] = {}
        self._servers = servers if servers is not None else get_mcp_servers()
        self._started = False

    @staticmethod
    def default() -> McpClientManager:
        """Return an MCP client manager loaded from mcp.config.json."""
        client = McpClientManager()
        return client

    @property
    def servers(self) -> tuple[McpServer, ...]:
        """Return configured MCP servers for this client."""
        return self._servers

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Invoke an MCP tool and return formatted text for the LLM."""
        route = self._routes.get(tool_name)
        if route is None:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        result = await route.session.call_tool(route.tool_name, arguments)
        content = self._format_call_tool_result(result)
        return content

    async def connect_server(self, server: McpServer) -> list[McpToolDefinition]:
        """Connect to an MCP server and register its tools."""
        if server.name in self._server_tools:
            definitions = self._server_tools[server.name]
            return definitions

        await self._ensure_started()
        session = await self._open_session(server)
        tools_result = await session.list_tools()
        definitions = self._register_tools(server, session, tools_result.tools)
        self._server_tools[server.name] = definitions
        logger.info(
            "mcp_server_connected",
            extra={"server_name": server.name, "tool_count": len(definitions)},
        )
        return definitions

    def servers_for_agent(self, server_names: list[str]) -> tuple[McpServer, ...]:
        """Return configured MCP servers referenced by name on an agent."""
        if not server_names:
            return ()

        servers_by_name = {server.name: server for server in self._servers}
        selected: list[McpServer] = []
        for name in server_names:
            server = servers_by_name.get(name)
            if server is None:
                raise ValueError(f"Unknown MCP server: {name}")
            selected.append(server)
        merged = tuple(selected)
        return merged

    async def shutdown(self) -> None:
        """Close all MCP sessions."""
        if not self._started:
            return
        await self._exit_stack.aclose()
        self._routes.clear()
        self._server_tools.clear()
        self._started = False

    async def _ensure_started(self) -> None:
        """Start the shared async exit stack once."""
        if self._started:
            return
        await self._exit_stack.__aenter__()
        self._started = True

    @staticmethod
    def _format_call_tool_result(result: mcp_types.CallToolResult) -> str:
        """Convert an MCP tool result into plain text for prompts."""
        parts: list[str] = []
        for content in result.content:
            if content.type == "text":
                parts.append(content.text)
            else:
                parts.append(str(content))

        text = "\n".join(part for part in parts if part)
        if result.isError:
            message = text or "MCP tool failed"
            error_text = f"Error: {message}"
            return error_text

        if not text:
            text = "OK"
        return text

    async def _open_session(self, server: McpServer) -> ClientSession:
        """Open and initialize a client session for one MCP server."""
        if server.transport == "stdio":
            session = await self._open_stdio_session(server)
            return session

        session = await self._open_streamable_http_session(server)
        return session

    async def _open_stdio_session(self, server: McpServer) -> ClientSession:
        """Connect to a local MCP server over stdio."""
        params = StdioServerParameters(
            args=server.args,
            command=server.command or "",
            cwd=server.cwd,
            env=server.env,
        )
        read_stream, write_stream = await self._exit_stack.enter_async_context(stdio_client(params))
        session_context = ClientSession(read_stream, write_stream)
        session = await self._exit_stack.enter_async_context(session_context)
        await session.initialize()
        return session

    async def _open_streamable_http_session(self, server: McpServer) -> ClientSession:
        """Connect to a remote MCP server over streamable HTTP."""
        timeout = httpx.Timeout(30.0, read=300.0)
        http_client = create_mcp_http_client(headers=server.headers, timeout=timeout)
        await self._exit_stack.enter_async_context(http_client)
        transport = streamable_http_client(url=server.url or "", http_client=http_client)
        read_stream, write_stream, _ = await self._exit_stack.enter_async_context(transport)
        session_context = ClientSession(read_stream, write_stream)
        session = await self._exit_stack.enter_async_context(session_context)
        await session.initialize()
        return session

    def _register_tools(
        self,
        server: McpServer,
        session: ClientSession,
        tools: list[mcp_types.Tool],
    ) -> list[McpToolDefinition]:
        """Register MCP tools under provider-safe prefixed names."""
        definitions: list[McpToolDefinition] = []
        for tool in tools:
            formatted_name = format_mcp_tool_name(server.name, tool.name)
            route = _McpToolRoute(session=session, tool_name=tool.name)
            self._routes[formatted_name] = route
            definition = McpToolDefinition(
                description=tool.description or f"MCP tool {tool.name} from {server.name}.",
                mcp_server_name=server.name,
                mcp_tool_name=tool.name,
                params_schema=tool.inputSchema,
            )
            definitions.append(definition)
        return definitions
