"""Unit tests for the local tool registry."""

import asyncio
from typing import Any

from agents.tools.registry import ToolRegistry
from agents.tools.types import ToolCall
from tests.agents.mock_data import DaysUntilDateTool


class TestToolRegistry:
    """Table-driven tests for ToolRegistry."""

    def test_execute(self) -> None:
        """Run execute scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "executes_days_until_date",
                "tool": DaysUntilDateTool(),
                "tool_call": ToolCall(
                    id="call_1",
                    name="days_until_date",
                    arguments={"event_date": "2099-01-01"},
                ),
                "expected_tool_call_id": "call_1",
                "content_is_digit": True,
            },
        ]

        for case in test_cases:
            # ARRANGE
            registry = ToolRegistry()
            registry.register(case["tool"])

            # ACT
            result = asyncio.run(registry.execute(case["tool_call"]))

            # ASSERT
            assert result.tool_call_id == case["expected_tool_call_id"]
            if case["content_is_digit"]:
                assert result.content.isdigit()
