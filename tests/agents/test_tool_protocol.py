"""Unit tests for the Tool protocol."""

from typing import Any

from agents.tools.protocols import Tool
from agents.tools.web_search import WebSearchTool
from tests.agents.mock_data import DaysUntilDateTool


class TestToolProtocol:
    """Table-driven tests for the Tool protocol."""

    def test_implementations_satisfy_protocol(self) -> None:
        """Run protocol compliance scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "web_search_tool",
                "tool": WebSearchTool(client=object()),
                "expected_name": "web_search",
            },
            {
                "name": "days_until_date_tool",
                "tool": DaysUntilDateTool(),
                "expected_name": "days_until_date",
            },
        ]

        for case in test_cases:
            # ARRANGE
            tool = case["tool"]

            # ACT
            definition = tool.definition()

            # ASSERT
            assert isinstance(tool, Tool)
            assert definition.name == case["expected_name"]
            assert definition.description
            assert definition.params_model
