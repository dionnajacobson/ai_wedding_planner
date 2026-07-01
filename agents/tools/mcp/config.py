"""MCP server connection types for agent tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SSEConfig(BaseModel):
    """Configuration for an SSE MCP server."""

    sse_read_timeout: int = 300
    timeout: int = 30
    url: str


class StdioConfig(BaseModel):
    """Configuration for a stdio MCP server."""

    args: list[str] = Field(default_factory=list)
    command: str
    env: dict[str, str] | None = None


class StreamableHttpConfig(BaseModel):
    """Configuration for a streamable HTTP MCP server."""

    headers: dict[str, str] | None = None
    url: str


class ServerConfig(BaseModel):
    """Configuration for one MCP server."""

    config: SSEConfig | StdioConfig | StreamableHttpConfig
    description: str = ""
    name: str
    type: Literal["sse", "stdio", "streamable_http"] = "stdio"

    @model_validator(mode="after")
    def validate_server_config(self) -> ServerConfig:
        """Require transport config to match the declared server type."""
        if self.type == "stdio" and not isinstance(self.config, StdioConfig):
            raise ValueError(f"MCP server '{self.name}' requires stdio config")
        if self.type == "sse" and not isinstance(self.config, SSEConfig):
            raise ValueError(f"MCP server '{self.name}' requires sse config")
        if self.type == "streamable_http" and not isinstance(self.config, StreamableHttpConfig):
            raise ValueError(f"MCP server '{self.name}' requires streamable_http config")
        return self


McpServer = ServerConfig
