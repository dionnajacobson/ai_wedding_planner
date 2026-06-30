"""End-to-end tests for the Apify MCP wedding vendor scraper."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agents.tools.mcp.client_manager import McpClientManager
from agents.tools.mcp.config import McpServer

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

APIFY_MCP_URL = (
    "https://mcp.apify.com?tools=fortuitous_pirate/wedding-vendor-scraper,get-actor-output"
)
WEDDING_VENDOR_TOOL = "mcp_apify_fortuitous_pirate_wedding_vendor_scraper"
WEDDING_VENDOR_MCP_NAME = "fortuitous_pirate--wedding-vendor-scraper"


def _apify_server() -> McpServer:
    """Build an enabled Apify MCP server from the environment token."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError("APIFY_API_TOKEN is required for Apify MCP e2e tests")

    server = McpServer(
        enabled=True,
        headers={"Authorization": f"Bearer {token}"},
        name="apify",
        transport="streamable_http",
        url=APIFY_MCP_URL,
    )
    return server


@pytest.mark.api
@pytest.mark.skipif(not os.getenv("APIFY_API_TOKEN"), reason="APIFY_API_TOKEN not set")
class TestApifyMcpE2E:
    """Live integration tests against the hosted Apify MCP server."""

    def test_connect_registers_wedding_vendor_scraper(self) -> None:
        """Connect to Apify MCP and expose the wedding vendor scraper tool."""
        server = _apify_server()

        async def run() -> list[str]:
            client = McpClientManager(servers=(server,))
            try:
                definitions = await client.connect_server(server)
                tool_names = [definition.mcp_tool_name for definition in definitions]
                return tool_names
            finally:
                await client.shutdown()

        tool_names = asyncio.run(run())

        assert WEDDING_VENDOR_MCP_NAME in tool_names

    def test_call_wedding_vendor_scraper(self) -> None:
        """Run the wedding vendor scraper Actor through Apify MCP."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_successful_actor_run",
                "arguments": {
                    "location": "Austin, TX",
                    "maxResults": 2,
                    "vendorType": "florist",
                },
                "expected_status": "SUCCEEDED",
            },
        ]

        server = _apify_server()

        for case in test_cases:
            # ARRANGE
            async def run() -> str:
                client = McpClientManager(servers=(server,))
                try:
                    await client.connect_server(server)
                    content = await client.call_tool(WEDDING_VENDOR_TOOL, case["arguments"])
                    return content
                finally:
                    await client.shutdown()

            # ACT
            content = asyncio.run(run())
            print(content)

            # ASSERT
            assert content
            assert not content.startswith("Error:")
            payload = json.loads(content.split("\n", 1)[0])
            assert payload["status"] == case["expected_status"]
            assert payload["actorName"] == "fortuitous_pirate/wedding-vendor-scraper"
