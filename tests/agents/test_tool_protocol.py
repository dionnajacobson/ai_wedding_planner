"""Unit tests for the ToolExecutor protocol."""

from typing import Any

from agents.tools.protocols import ToolExecutor
from agents.tools.tools.web_search import WebSearchDefinition, WebSearchExecutor
from agents.tools.types import ToolName
from tests.agents.mock_data import DaysUntilDateDefinition, DaysUntilDateExecutor


class TestToolExecutorProtocol:
    """Table-driven tests for the ToolExecutor protocol."""

    def test_implementations_satisfy_protocol(self) -> None:
        """Run protocol compliance scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "web_search_executor",
                "executor": WebSearchExecutor(client=object()),
            },
            {
                "name": "days_until_date_executor",
                "executor": DaysUntilDateExecutor(),
            },
        ]

        for case in test_cases:
            executor = case["executor"]
            assert isinstance(executor, ToolExecutor)


class TestToolDefinitions:
    """Table-driven tests for tool definition schemas."""

    def test_definitions_are_valid(self) -> None:
        """Run definition validation scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "web_search",
                "definition": WebSearchDefinition(),
                "expected_name": ToolName.WEB_SEARCH,
            },
            {
                "name": "days_until_date",
                "definition": DaysUntilDateDefinition(),
                "expected_name": ToolName.DAYS_UNTIL_DATE,
            },
        ]

        for case in test_cases:
            definition = case["definition"]
            assert definition.name == case["expected_name"]
            assert definition.description
            assert definition.params_model
