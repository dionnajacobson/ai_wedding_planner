"""Simple agent configuration and tool loop runner."""

from __future__ import annotations

import logging

from agents.agent.types import Agent, AgentRunResult
from agents.client import LLMClient
from agents.client.types import LLMRequest, LLMResponse
from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.types import ToolCall, ToolDefinition, ToolResult

logger = logging.getLogger(__name__)


class AgentRunner:
    """Run an agent through the LLM + tool loop."""

    def __init__(
        self,
        client: LLMClient,
        tool_orchestrator: ToolOrchestrator,
    ) -> None:
        """Initialize the runner with an LLM client and tool orchestrator."""
        self._client = client
        self._tool_orchestrator = tool_orchestrator

    @staticmethod
    def default() -> AgentRunner:
        """Get the default agent runner."""
        client = LLMClient.default()
        tool_orchestrator = ToolOrchestrator.default()
        runner = AgentRunner(client, tool_orchestrator)
        return runner

    async def run(self, agent: Agent) -> AgentRunResult:
        """Run the agent until it returns text or hits the tool round limit."""
        entries = await self._tool_orchestrator.prepare(agent)
        llm_tools = [entry.definition for entry in entries] or None

        tool_results: list[ToolResult] = []
        response: LLMResponse | None = None
        tool_rounds = 0

        for round_number in range(1, agent.max_tool_rounds + 1):
            response = self._invoke(agent, tool_results, llm_tools)
            if not response.tool_calls:
                break

            tool_rounds += 1
            self._log_tool_round(agent.name, round_number, response.tool_calls)
            round_results = await self._tool_orchestrator.execute_all(
                response.tool_calls,
                entries=entries,
                runner=self,
            )
            tool_results.extend(round_results)

        result = self._build_result(response, tool_results, tool_rounds)
        return result

    async def shutdown(self) -> None:
        """Release resources (e.g. MCP sessions) held by the tool orchestrator."""
        await self._tool_orchestrator.shutdown()

    def _invoke(
        self,
        agent: Agent,
        tool_results: list[ToolResult],
        tools: list[ToolDefinition] | None,
    ) -> LLMResponse:
        """Render the prompt and call the LLM for one turn."""
        agent.prompt.update_context(tool_results=tool_results)
        rendered_prompt = agent.prompt.render()
        request = LLMRequest(
            max_tokens=agent.max_tokens,
            model=agent.model,
            system=rendered_prompt.system,
            tools=tools,
            user=rendered_prompt.user,
        )
        response = self._client.invoke(request=request)
        return response

    @staticmethod
    def _build_result(
        response: LLMResponse | None,
        tool_results: list[ToolResult],
        tool_rounds: int,
    ) -> AgentRunResult:
        """Build the final run result from the last LLM response and tool history."""
        content = response.content if response else None
        content = content or "I couldn't generate a response."
        result = AgentRunResult(
            content=content,
            tool_rounds=tool_rounds,
            tool_results=tool_results,
        )
        return result

    @staticmethod
    def _log_tool_round(
        agent_name: str,
        round_number: int,
        tool_calls: list[ToolCall],
    ) -> None:
        """Log the start of a tool execution round."""
        logger.info(
            "tool_round_started",
            extra={
                "agent": agent_name,
                "round_number": round_number,
                "tool_count": len(tool_calls),
                "tool_names": [tool_call.name for tool_call in tool_calls],
            },
        )
