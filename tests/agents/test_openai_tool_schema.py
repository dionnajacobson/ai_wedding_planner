"""Unit tests for OpenAI MCP tool schema formatting."""

from __future__ import annotations

from typing import Any

from agents.client.openai.adapter import OpenAIAdapter
from agents.tools.mcp.definitions import McpToolDefinition
from agents.tools.types import ToolName


class TestOpenAIToolSchema:
    """Table-driven tests for OpenAI function schema normalization."""

    def test_format_tool_normalizes_mcp_schema(self) -> None:
        """Run MCP schema formatting scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "adds_additional_properties_false",
                "definition": McpToolDefinition(
                    description="Scrape wedding vendors",
                    mcp_server_name="apify",
                    mcp_tool_name="fortuitous_pirate--wedding-vendor-scraper",
                    params_schema={
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "maxResults": {"type": "integer"},
                            "vendorType": {"type": "string"},
                        },
                        "required": ["location"],
                    },
                ),
                "expected_strict": False,
            },
        ]

        adapter = OpenAIAdapter(client=object())  # type: ignore[arg-type]

        for case in test_cases:
            formatted = adapter._format_tool(case["definition"])

            assert formatted["strict"] is case["expected_strict"]
            assert formatted["parameters"]["additionalProperties"] is False

    def test_format_tool_keeps_strict_mode_for_pydantic_tools(self) -> None:
        """Built-in Pydantic-backed tools remain strict."""
        from agents.tools.tools.web_search import WebSearchDefinition

        adapter = OpenAIAdapter(client=object())  # type: ignore[arg-type]

        formatted = adapter._format_tool(WebSearchDefinition())

        assert formatted["strict"] is True
        assert formatted["name"] == ToolName.WEB_SEARCH.value
