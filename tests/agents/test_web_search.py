"""Unit tests for the Tavily web search tool."""

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from dotenv import load_dotenv

from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.types import ToolCall, ToolName
from agents.tools.web_search import WebSearchExecutor

load_dotenv()


class TestWebSearchTool:
    """Table-driven tests for WebSearchTool."""

    def test_format_search_results(self) -> None:
        """Run format-search-results scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "includes_answer_and_sources",
                "response": {
                    "answer": "Average cost is $30,000.",
                    "results": [
                        {
                            "title": "Wedding costs",
                            "content": "National average rose in 2025.",
                            "url": "https://example.com/costs",
                        }
                    ],
                },
                "expected_fragments": [
                    "Average cost is $30,000.",
                    "Wedding costs",
                    "https://example.com/costs",
                ],
            },
            {
                "name": "returns_message_when_no_results",
                "response": {"results": []},
                "expected_fragments": ["No results found."],
            },
        ]

        tool = WebSearchExecutor(client=MagicMock())

        for case in test_cases:
            # ACT
            text = tool._format_search_results(case["response"])

            # ASSERT
            for fragment in case["expected_fragments"]:
                assert fragment in text

    def test_search(self) -> None:
        """Run search scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "calls_tavily_client",
                "query": "Austin wedding venues",
                "search_response": {
                    "results": [{"title": "Venues", "content": "Top venues in Austin.", "url": ""}]
                },
                "expected_query": "Austin wedding venues",
                "expected_fragment": "Top venues in Austin.",
            },
        ]

        for case in test_cases:
            # ARRANGE
            client = MagicMock()
            client.search = AsyncMock(return_value=case["search_response"])
            tool = WebSearchExecutor(client=client)

            # ACT
            text = asyncio.run(tool._search(case["query"]))

            # ASSERT
            client.search.assert_awaited_once_with(
                query=case["expected_query"],
                max_results=5,
            )
            assert case["expected_fragment"] in text

    def test_registry_execute(self) -> None:
        """Run registry execute scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "executes_web_search",
                "search_response": {
                    "results": [
                        {"title": "Florists", "content": "Best florists nearby.", "url": ""}
                    ]
                },
                "tool_call": ToolCall(
                    id="call_1",
                    name="web_search",
                    arguments={"query": "local wedding florists"},
                ),
                "expected_tool_call_id": "call_1",
                "expected_fragment": "Best florists nearby.",
            },
        ]

        for case in test_cases:
            # ARRANGE
            client = MagicMock()
            client.search = AsyncMock(return_value=case["search_response"])
            orchestrator = ToolOrchestrator(
                {ToolName.WEB_SEARCH: WebSearchExecutor(client=client)},
            )

            # ACT
            result = asyncio.run(orchestrator.execute(case["tool_call"]))

            # ASSERT
            assert result.tool_call_id == case["expected_tool_call_id"]
            assert case["expected_fragment"] in result.content


@pytest.mark.skipif(not os.getenv("TAVILY_API_KEY"), reason="TAVILY_API_KEY not set")
class TestWebSearchToolE2E:
    """End-to-end table-driven tests for WebSearchTool against the Tavily API."""

    def test_search_e2e(self) -> None:
        """Run live Tavily search scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_results_for_wedding_query",
                "query": "average wedding cost United States",
                "reject_content": "No results found.",
            },
        ]

        tool = WebSearchExecutor()

        for case in test_cases:
            # ACT
            content = asyncio.run(tool._search(case["query"]))

            # ASSERT
            assert content
            assert case["reject_content"] not in content
            assert content.startswith("Answer:") or content.startswith("- ")
