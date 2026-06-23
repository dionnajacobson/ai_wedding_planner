"""Shared fixtures for agent tests."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from agents.tools.protocols import Tool
from agents.tools.types import ToolCall, ToolDefinition, ToolResult


class DaysUntilDateInput(BaseModel):
    """Input schema for the days_until_date tool."""

    event_date: str = Field(description="Target date in YYYY-MM-DD format.")


class DaysUntilDateTool(Tool):
    """Calculate how many days remain until a wedding or event date."""

    def definition(self) -> ToolDefinition:
        """Return the days_until_date tool schema."""
        definition = ToolDefinition(
            name="days_until_date",
            description="Calculate how many days remain until a wedding or event date.",
            params_model=DaysUntilDateInput,
        )
        return definition

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """Return the number of days from today until the given date."""
        params = DaysUntilDateInput.model_validate(tool_call.arguments)
        target = date.fromisoformat(params.event_date)
        days = (target - date.today()).days
        content = str(days)
        result = ToolResult(tool_call_id=tool_call.id, content=content)
        return result
