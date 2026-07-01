"""Days until a target date tool."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolDefinition, ToolName, ToolResult

if TYPE_CHECKING:
    from agents.agent.types import ToolEntry


class DaysUntilDateInput(BaseModel):
    """Input schema for the days_until_date tool."""

    event_date: str = Field(description="Target date in YYYY-MM-DD format.")


class DaysUntilDateDefinition(ToolDefinition):
    """Schema exposed to the LLM for the days_until_date tool."""

    description: str = "Calculate how many days remain until a wedding or event date."
    name: ToolName = ToolName.DAYS_UNTIL_DATE
    params_model: type[BaseModel] = DaysUntilDateInput


class DaysUntilDateExecutor(ToolExecutor):
    """Calculate how many days remain until a wedding or event date."""

    async def execute(
        self,
        tool_call: ToolCall,
        tool_entry: ToolEntry,
        runner: Any,
    ) -> ToolResult:
        """Return the number of days from today until the given date."""
        params = DaysUntilDateInput.model_validate(tool_call.arguments)
        target = date.fromisoformat(params.event_date)
        days = (target - date.today()).days
        content = str(days)
        result = ToolResult(content=content, tool_call_id=tool_call.id)
        return result
