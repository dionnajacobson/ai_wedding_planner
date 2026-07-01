"""MCP client session management for agent tool execution."""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any

import httpx
import mcp.types as mcp_types
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from agents.tools.mcp.config import (
    SSEConfig,
    ServerConfig,
    StdioConfig,
    StreamableHttpConfig,
)
from agents.tools.mcp.definitions import McpToolDefinition

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _McpToolRoute:
    """Route a provider-facing MCP tool name to a live session."""

    session: ClientSession
    tool_name: str


class McpClientManager:
    """Connect to MCP servers and expose their tools to agents."""

    def __init__(self) -> None:
        """Initialize an MCP client manager."""
        self._exit_stack = AsyncExitStack()
        self._routes: dict[str, _McpToolRoute] = {}
        self._server_tools: dict[str, list[McpToolDefinition]] = {}
        self._started = False

    @classmethod
    def default(cls) -> McpClientManager:
        """Return the default MCP client manager."""
        return cls()

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Invoke an MCP tool and return formatted text for the LLM."""
        route = self._routes.get(tool_name)
        if route is None:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        result = await route.session.call_tool(route.tool_name, arguments)
        return self._format_call_tool_result(result)

    async def connect_server(self, server: ServerConfig) -> list[McpToolDefinition]:
        """Connect to one MCP server and register its tools."""
        if server.name in self._server_tools:
            return self._server_tools[server.name]

        await self._ensure_started()
        session = await self._connect_to_server(server)
        tools_result = await session.list_tools()
        definitions = self._register_tools(server, session, tools_result.tools)
        self._server_tools[server.name] = definitions
        logger.info(
            "mcp_server_connected",
            extra={"server_name": server.name, "tool_count": len(definitions)},
        )
        return definitions

    def resolve_servers(
        self,
        tool_servers: tuple[ServerConfig, ...] | list[ServerConfig],
    ) -> tuple[ServerConfig, ...]:
        """Return MCP servers declared on an agent tool list."""
        return tuple(tool_servers)

    async def shutdown(self) -> None:
        """Close all MCP sessions."""
        if not self._started:
            return
        await self._exit_stack.aclose()
        self._routes.clear()
        self._server_tools.clear()
        self._started = False

    async def _connect_to_server(self, server: ServerConfig) -> ClientSession:
        """Open a transport, initialize a session, and register native tool routes."""
        if server.type == "streamable_http":
            return await self._open_streamable_http_session(server)

        transport = self._open_transport(server)
        read_stream, write_stream = await self._exit_stack.enter_async_context(transport)
        session_context = ClientSession(read_stream, write_stream)
        session = await self._exit_stack.enter_async_context(session_context)
        await session.initialize()
        return session

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
            return f"Error: {message}"

        return text or "OK"

    def _open_transport(self, server: ServerConfig):
        """Return the async context manager for stdio or SSE transports."""
        if server.type == "stdio":
            stdio_config = server.config
            if not isinstance(stdio_config, StdioConfig):
                raise ValueError(f"MCP server '{server.name}' requires stdio config")
            params = StdioServerParameters(
                args=stdio_config.args,
                command=stdio_config.command,
                env=stdio_config.env,
            )
            return stdio_client(params)

        sse_config = server.config
        if not isinstance(sse_config, SSEConfig):
            raise ValueError(f"MCP server '{server.name}' requires sse config")
        return sse_client(
            url=sse_config.url,
            sse_read_timeout=sse_config.sse_read_timeout,
            timeout=sse_config.timeout,
        )

    async def _open_streamable_http_session(self, server: ServerConfig) -> ClientSession:
        """Connect to a remote MCP server over streamable HTTP."""
        streamable_config = server.config
        if not isinstance(streamable_config, StreamableHttpConfig):
            raise ValueError(f"MCP server '{server.name}' requires streamable_http config")

        timeout = httpx.Timeout(30.0, read=300.0)
        http_client = create_mcp_http_client(
            headers=streamable_config.headers,
            timeout=timeout,
        )
        await self._exit_stack.enter_async_context(http_client)
        transport = streamable_http_client(
            url=streamable_config.url,
            http_client=http_client,
        )
        read_stream, write_stream, _ = await self._exit_stack.enter_async_context(transport)
        session_context = ClientSession(read_stream, write_stream)
        session = await self._exit_stack.enter_async_context(session_context)
        await session.initialize()
        return session

    def _register_tools(
        self,
        server: ServerConfig,
        session: ClientSession,
        tools: list[mcp_types.Tool],
    ) -> list[McpToolDefinition]:
        """Register MCP tools under provider-safe prefixed names."""
        definitions: list[McpToolDefinition] = []
        for tool in tools:
            formatted_name = McpToolDefinition.format_name(server.name, tool.name)
            self._routes[formatted_name] = _McpToolRoute(session=session, tool_name=tool.name)
            definitions.append(
                McpToolDefinition(
                    description=tool.description or f"MCP tool {tool.name} from {server.name}.",
                    mcp_server_name=server.name,
                    mcp_tool_name=tool.name,
                    params_schema=tool.inputSchema,
                )
            )
        return definitions
