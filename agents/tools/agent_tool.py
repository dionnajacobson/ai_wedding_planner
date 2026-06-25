"""Executor for agents exposed as tools via AgentRunner.agent_to_tool_definition()."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolResult

if TYPE_CHECKING:
    from agents.agent.agent import AgentRunner
    from agents.agent.types import Agent


class AgentToolInput(BaseModel):
    """Input schema for invoking an agent as a tool."""

    task: str = Field(description="Task or question for the sub-agent to complete.")


class AgentToolExecutor(ToolExecutor):
    """Run an agent after applying validated tool call input to its prompt."""

    def __init__(self, runner: Any | None = None) -> None:
        """Optionally pin a runner for tests; production passes runner per execute call."""
        self._runner = runner

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        agents: dict[str, Agent] | None = None,
        runner: AgentRunner | None = None,
    ) -> ToolResult:
        """Validate input, update the agent prompt, run it, and return its reply."""
        active_runner = self._runner or runner
        if agents is None or tool_call.tool_key is None or active_runner is None:
            raise ValueError(
                "Agent tool calls require an agent registry, tool_key, and runner.",
            )

        params = AgentToolInput.model_validate(tool_call.arguments)
        agent = agents[tool_call.tool_key]
        agent.prompt.runtime_context.clear()
        agent.prompt.update_context(**params.model_dump())
        run_result = await active_runner.run(agent)
        return ToolResult(tool_call_id=tool_call.id, content=run_result.content)
