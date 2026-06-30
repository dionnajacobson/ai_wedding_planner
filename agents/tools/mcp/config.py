"""MCP server connection configuration for agent tools."""

from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
MCP_CONFIG_FILENAME = "mcp.config.json"


class McpServer(BaseModel):
    """Configuration for connecting an agent to an MCP server."""

    args: list[str] = Field(default_factory=list)
    command: str | None = None
    cwd: str | None = None
    enabled: bool = True
    env: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    name: str = Field(description="Logical name used to prefix MCP tool names.")
    transport: Literal["stdio", "streamable_http"] = "stdio"
    url: str | None = None

    @model_validator(mode="after")
    def validate_transport_fields(self) -> McpServer:
        """Require transport-specific connection fields."""
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio MCP servers require command")
        if self.transport == "streamable_http" and not self.url:
            raise ValueError("streamable_http MCP servers require url")
        return self


class McpConfigFile(BaseModel):
    """Root shape of mcp.config.json."""

    mcp_servers: list[McpServer] = Field(default_factory=list)


def find_project_root() -> Path:
    """Locate the project root by walking up to pyproject.toml."""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    message = "Could not locate project root for MCP config"
    raise RuntimeError(message)


def get_mcp_config_path() -> Path:
    """Resolve the MCP config file path."""
    env_path = os.getenv("MCP_CONFIG_PATH")
    if env_path:
        resolved = Path(env_path).expanduser()
        return resolved

    resolved = find_project_root() / MCP_CONFIG_FILENAME
    return resolved


@lru_cache
def get_mcp_config() -> McpConfigFile:
    """Load and validate MCP settings once per process."""
    config_path = get_mcp_config_path()
    if not config_path.exists():
        logger.info("mcp_config_not_found", extra={"path": str(config_path)})
        config = McpConfigFile()
        return config

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    expanded = expand_env_vars(raw)
    config = McpConfigFile.model_validate(expanded)
    logger.info(
        "mcp_config_loaded",
        extra={"path": str(config_path), "server_count": len(config.mcp_servers)},
    )
    return config


@lru_cache
def get_mcp_servers() -> tuple[McpServer, ...]:
    """Return enabled MCP servers declared in mcp.config.json."""
    config = get_mcp_config()
    servers = tuple(server for server in config.mcp_servers if server.enabled)
    return servers


def expand_env_vars(value: Any) -> Any:
    """Replace ${VAR_NAME} placeholders with environment variable values."""
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            variable_name = match.group(1)
            env_value = os.getenv(variable_name)
            if env_value is None:
                raise ValueError(
                    f"Missing environment variable referenced in MCP config: {variable_name}"
                )
            return env_value

        expanded = ENV_VAR_PATTERN.sub(replace, value)
        return expanded

    if isinstance(value, dict):
        expanded_dict = {key: expand_env_vars(item) for key, item in value.items()}
        return expanded_dict

    if isinstance(value, list):
        expanded_list = [expand_env_vars(item) for item in value]
        return expanded_list

    return value


def reset_mcp_config_cache() -> None:
    """Clear cached MCP config (for tests)."""
    get_mcp_config.cache_clear()
    get_mcp_servers.cache_clear()
