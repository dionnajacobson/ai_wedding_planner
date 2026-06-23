"""Unit tests for the local tool registry."""

from datetime import date

from agents.tools.registry import ToolRegistry
from agents.tools.types import ToolCall
from tests.agents.mock_data import DaysUntilDateInput, mock_days_until_date_tool


def _days_until_date_handler(params: DaysUntilDateInput) -> str:
    target = date.fromisoformat(params.event_date)
    days = (target - date.today()).days
    result = str(days)
    return result


def test_registry_executes_days_until_date() -> None:
    registry = ToolRegistry()
    registry.register(mock_days_until_date_tool(), _days_until_date_handler)
    result = registry.execute(
        ToolCall(
            id="call_1",
            name="days_until_date",
            arguments={"event_date": "2099-01-01"},
        )
    )

    assert result.tool_call_id == "call_1"
    assert result.content.isdigit()
