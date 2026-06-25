"""Unit tests for the tool orchestrator."""

import asyncio
from typing import Any

from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.types import ToolCall, ToolName
from tests.agents.mock_data import DaysUntilDateExecutor


class TestToolOrchestrator:
    """Table-driven tests for ToolOrchestrator."""

    def test_execute(self) -> None:
        """Run execute scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "executes_days_until_date",
                "executor": DaysUntilDateExecutor(),
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
            orchestrator = ToolOrchestrator(
                {ToolName.DAYS_UNTIL_DATE: case["executor"]},
            )

            # ACT
            result = asyncio.run(orchestrator.execute(case["tool_call"]))

            # ASSERT
            assert result.tool_call_id == case["expected_tool_call_id"]
            if case["content_is_digit"]:
                assert result.content.isdigit()
