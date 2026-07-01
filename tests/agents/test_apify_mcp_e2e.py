"""End-to-end tests for the Apify MCP wedding vendor scraper."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agents.tools.mcp.apify import ApifyMcpServer
from agents.tools.mcp.client_manager import McpClientManager

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

WEDDING_VENDOR_TOOL = "mcp_apify_fortuitous_pirate_wedding_vendor_scraper"
WEDDING_VENDOR_MCP_NAME = "fortuitous_pirate--wedding-vendor-scraper"


def _apify_server():
    """Return the Apify MCP server definition."""
    return ApifyMcpServer


@pytest.mark.api
@pytest.mark.skipif(not os.getenv("APIFY_API_TOKEN"), reason="APIFY_API_TOKEN not set")
class TestApifyMcpE2E:
    """Live integration tests against the hosted Apify MCP server."""

    def test_connect_registers_wedding_vendor_scraper(self) -> None:
        """Connect to Apify MCP and expose the wedding vendor scraper tool."""
        server = _apify_server()

        async def run() -> list[str]:
            client = McpClientManager()
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
                client = McpClientManager()
                try:
                    await client.connect_server(server)
                    content = await client.call_tool(WEDDING_VENDOR_TOOL, case["arguments"])
                    return content
                finally:
                    await client.shutdown()

            # ACT
            content = asyncio.run(run())

            # ASSERT
            assert content
            assert not content.startswith("Error:")
            payload = json.loads(content.split("\n", 1)[0])
            assert payload["status"] == case["expected_status"]
            assert payload["actorName"] == "fortuitous_pirate/wedding-vendor-scraper"
