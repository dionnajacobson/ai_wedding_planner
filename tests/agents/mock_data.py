"""Shared fixtures for agent tests."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agents.tools.types import ToolDefinition


class DaysUntilDateInput(BaseModel):
    """Input schema for the days_until_date tool."""

    event_date: str = Field(description="Target date in YYYY-MM-DD format.")


def mock_days_until_date_tool() -> ToolDefinition:
    """Build the days_until_date tool definition."""
    return ToolDefinition(
        name="days_until_date",
        description="Calculate how many days remain until a wedding or event date.",
        params_model=DaysUntilDateInput,
    )
