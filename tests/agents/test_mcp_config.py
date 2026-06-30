"""Unit tests for MCP config.json loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agents.tools.mcp.config import (
    McpServer,
    expand_env_vars,
    get_mcp_config,
    get_mcp_servers,
    reset_mcp_config_cache,
)


class TestMcpConfigLoader:
    """Table-driven tests for mcp.config.json loading."""

    def setup_method(self) -> None:
        """Clear cached MCP config before each test."""
        reset_mcp_config_cache()

    def teardown_method(self) -> None:
        """Clear cached MCP config after each test."""
        reset_mcp_config_cache()

    def test_get_mcp_servers_from_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Run config loading scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "loads_enabled_stdio_server",
                "config": {
                    "mcp_servers": [
                        {
                            "name": "filesystem",
                            "enabled": True,
                            "transport": "stdio",
                            "command": "npx",
                            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                        }
                    ]
                },
                "expected_count": 1,
                "expected_name": "filesystem",
            },
            {
                "name": "skips_disabled_servers",
                "config": {
                    "mcp_servers": [
                        {
                            "name": "filesystem",
                            "enabled": False,
                            "transport": "stdio",
                            "command": "npx",
                        }
                    ]
                },
                "expected_count": 0,
                "expected_name": None,
            },
        ]

        for case in test_cases:
            reset_mcp_config_cache()
            config_path = tmp_path / f"{case['name']}.json"
            config_path.write_text(json.dumps(case["config"]), encoding="utf-8")
            monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))

            servers = get_mcp_servers()

            assert len(servers) == case["expected_count"]
            if case["expected_name"] is not None:
                assert servers[0].name == case["expected_name"]

    def test_get_mcp_config_validates_transport(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Reject MCP servers that omit required transport fields."""
        config_path = tmp_path / "invalid.json"
        config_path.write_text(
            json.dumps({"mcp_servers": [{"name": "broken", "transport": "stdio"}]}),
            encoding="utf-8",
        )
        monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))

        with pytest.raises(ValueError, match="stdio MCP servers require command"):
            get_mcp_config()

    def test_get_mcp_servers_returns_empty_when_file_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Return an empty tuple when the config file does not exist."""
        missing_path = tmp_path / "missing.json"
        monkeypatch.setenv("MCP_CONFIG_PATH", str(missing_path))
        servers = get_mcp_servers()
        assert servers == ()

    def test_expand_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Replace ${VAR} placeholders in config values."""
        monkeypatch.setenv("MCP_AUTH_TOKEN", "secret-token")
        expanded = expand_env_vars({"headers": {"Authorization": "Bearer ${MCP_AUTH_TOKEN}"}})
        assert expanded["headers"]["Authorization"] == "Bearer secret-token"

    def test_expand_env_vars_raises_for_missing_variable(self) -> None:
        """Fail fast when a referenced environment variable is missing."""
        with pytest.raises(ValueError, match="Missing environment variable"):
            expand_env_vars("Bearer ${MISSING_MCP_TOKEN}")

    def test_mcp_server_supports_streamable_http(self) -> None:
        """Accept streamable HTTP MCP server settings."""
        server = McpServer(
            headers={"Authorization": "Bearer token"},
            name="remote",
            transport="streamable_http",
            url="https://example.com/mcp",
        )
        assert server.url == "https://example.com/mcp"

    def test_get_mcp_servers_loads_apify_vendor_scraper(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Load Apify MCP server settings for the wedding vendor scraper."""
        monkeypatch.setenv("APIFY_API_TOKEN", "apify-token")
        config_path = tmp_path / "apify.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcp_servers": [
                        {
                            "name": "apify",
                            "enabled": True,
                            "transport": "streamable_http",
                            "url": (
                                "https://mcp.apify.com?"
                                "tools=fortuitous_pirate/wedding-vendor-scraper,get-actor-output"
                            ),
                            "headers": {
                                "Authorization": "Bearer ${APIFY_API_TOKEN}",
                            },
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))

        servers = get_mcp_servers()

        assert len(servers) == 1
        assert servers[0].name == "apify"
        assert servers[0].headers == {"Authorization": "Bearer apify-token"}
        assert "fortuitous_pirate/wedding-vendor-scraper" in (servers[0].url or "")

    def test_get_mcp_servers_is_cached(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Load MCP config once per process."""
        config_path = tmp_path / "cached.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcp_servers": [
                        {
                            "name": "filesystem",
                            "transport": "stdio",
                            "command": "npx",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("MCP_CONFIG_PATH", str(config_path))

        first = get_mcp_servers()
        config_path.write_text(json.dumps({"mcp_servers": []}), encoding="utf-8")
        second = get_mcp_servers()

        assert first == second
        assert len(first) == 1
