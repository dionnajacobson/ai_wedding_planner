"""Apify MCP server for wedding vendor search."""

from __future__ import annotations

import os

from agents.tools.mcp.config import McpServer, StreamableHttpConfig

APIFY_MCP_URL = (
    "https://mcp.apify.com?tools=fortuitous_pirate/wedding-vendor-scraper,get-actor-output"
)

ApifyMcpServer = McpServer(
    name="apify",
    description="Apify wedding vendor scraper",
    type="streamable_http",
    config=StreamableHttpConfig(
        url=APIFY_MCP_URL,
        headers={"Authorization": f"Bearer {os.getenv('APIFY_API_TOKEN', '')}"},
    ),
)
