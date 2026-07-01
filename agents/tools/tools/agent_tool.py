"""Executor for agents exposed as tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolDefinition, ToolResult

if TYPE_CHECKING:
    from agents.agent.agent import AgentRunner
    from agents.agent.types import Agent


class AgentToolInput(BaseModel):
    """Input schema for invoking an agent as a tool."""

    task: str = Field(description="Task or question for the sub-agent to complete.")


class AgentToolDefinition(ToolDefinition):
    """Schema-only tool definition for an agent exposed as a tool."""

    agent_name: str

    @property
    def provider_name(self) -> str:
        """Return the provider-facing tool name."""
        provider_name = f"{self.name.value}_{self.agent_name}"
        return provider_name


class AgentToolExecutor(ToolExecutor):
    """Run an agent after applying validated tool call input to its prompt."""

    def __init__(self, runner: Any | None = None) -> None:
        """Optionally pin a runner for tests; production passes runner per execute call."""
        self._runner = runner

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agent: Agent | None = None,
        runner: AgentRunner | None = None,
    ) -> ToolResult:
        """Validate input, update the agent prompt, run it, and return its reply."""
        active_runner = self._runner or runner
        if agent is None or active_runner is None:
            raise ValueError("Agent tool calls require an agent and runner.")

        params = AgentToolInput.model_validate(tool_call.arguments)
        agent.prompt.runtime_context.clear()
        agent.prompt.update_context(**params.model_dump())
        run_result = await active_runner.run(agent)
        result = ToolResult(content=run_result.content, tool_call_id=tool_call.id)
        return result
