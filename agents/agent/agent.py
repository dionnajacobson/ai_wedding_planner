"""Simple agent configuration and tool loop runner."""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field

from agents.agent.types import AgentRunResult
from agents.client import LLMClient
from agents.client.types import LLMRequest, LLMResponse, Model
from agents.prompts.base import JinjaPrompt
from agents.tools.registry import ToolRegistry
from agents.tools.types import ToolDefinition, ToolResult

logger = logging.getLogger(__name__)


class Agent(BaseModel):
    """Configuration for a single LLM agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    model: Model
    prompt: JinjaPrompt
    tools: list[ToolDefinition] = Field(default_factory=list)
    max_tool_rounds: int = Field(default=10, ge=1)
    max_tokens: int = Field(default=1024, ge=1)


class AgentRunner:
    """Run an agent through the LLM + tool loop."""

    def __init__(self, client: LLMClient, tool_registry: ToolRegistry) -> None:
        """Initialize the runner with an LLM client and tool registry."""
        self._client = client
        self._tool_registry = tool_registry

    @staticmethod
    def default() -> AgentRunner:
        """Get the default agent runner."""
        client = LLMClient.default()
        tool_registry = ToolRegistry.default()
        runner = AgentRunner(client, tool_registry)
        return runner

    async def run(self, agent: Agent) -> AgentRunResult:
        """Run the agent until it returns text or hits the tool round limit."""
        prompt = agent.prompt
        tool_results: list[ToolResult] = []
        response: LLMResponse | None = None
        tool_rounds = 0

        for round_number in range(1, agent.max_tool_rounds + 1):
            prompt.update_context(tool_results=tool_results)
            rendered_prompt = prompt.render()
            request = LLMRequest(
                system=rendered_prompt.system,
                user=rendered_prompt.user,
                model=agent.model,
                tools=agent.tools or None,
                max_tokens=agent.max_tokens,
            )
            response = self._client.invoke(request=request)

            if not response.tool_calls:
                break

            tool_rounds += 1
            tool_names = [tool_call.name for tool_call in response.tool_calls]
            logger.info(
                "tool_round_started",
                extra={
                    "agent": agent.name,
                    "round_number": round_number,
                    "tool_count": len(response.tool_calls),
                    "tool_names": tool_names,
                },
            )
            round_results = await self._tool_registry.execute_all(response.tool_calls)
            tool_results.extend(round_results)

        content = response.content if response else None
        content = content or "I couldn't generate a response."
        result = AgentRunResult(
            content=content,
            tool_rounds=tool_rounds,
            tool_results=tool_results,
        )
        return result
