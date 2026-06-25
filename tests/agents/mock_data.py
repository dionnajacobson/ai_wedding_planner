"""Shared fixtures for agent tests."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolDefinition, ToolName, ToolResult

if TYPE_CHECKING:
    from agents.agent.types import Agent


class DaysUntilDateInput(BaseModel):
    """Input schema for the days_until_date tool."""

    event_date: str = Field(description="Target date in YYYY-MM-DD format.")


class DaysUntilDateDefinition(ToolDefinition):
    """Schema exposed to the LLM for the days_until_date tool."""

    name: ToolName = ToolName.DAYS_UNTIL_DATE
    description: str = "Calculate how many days remain until a wedding or event date."
    params_model: type[BaseModel] = DaysUntilDateInput


class DaysUntilDateExecutor(ToolExecutor):
    """Calculate how many days remain until a wedding or event date."""

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agents: dict[str, Agent] | None = None,
        runner: Any | None = None,
    ) -> ToolResult:
        """Return the number of days from today until the given date."""
        params = DaysUntilDateInput.model_validate(tool_call.arguments)
        target = date.fromisoformat(params.event_date)
        days = (target - date.today()).days
        content = str(days)
        result = ToolResult(tool_call_id=tool_call.id, content=content)
        return result
