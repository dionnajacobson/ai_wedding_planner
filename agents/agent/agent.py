"""Simple agent configuration and tool loop runner."""

from __future__ import annotations

import logging

from agents.agent.types import Agent, AgentRunResult, PreparedTools
from agents.client import LLMClient
from agents.client.types import LLMRequest, LLMResponse
from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.types import (
    AgentToolDefinition,
    ToolCall,
    ToolDefinition,
    ToolName,
    ToolResult,
    format_agent_name,
)

logger = logging.getLogger(__name__)


class AgentRunner:
    """Run an agent through the LLM + tool loop."""

    def __init__(self, client: LLMClient, tool_orchestrator: ToolOrchestrator) -> None:
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
        prompt = agent.prompt
        tool_results: list[ToolResult] = []
        response: LLMResponse | None = None
        tool_rounds = 0

        prepared = self._prepare_tools(agent.tools)
        tools = list(prepared.definitions.values()) or None

        for round_number in range(1, agent.max_tool_rounds + 1):
            prompt.update_context(tool_results=tool_results)
            rendered_prompt = prompt.render()
            request = LLMRequest(
                system=rendered_prompt.system,
                user=rendered_prompt.user,
                model=agent.model,
                tools=tools,
                max_tokens=agent.max_tokens,
            )
            response = self._client.invoke(request=request)

            if not response.tool_calls:
                break

            tool_rounds += 1
            logger.info(
                "tool_round_started",
                extra={
                    "agent": agent.name,
                    "round_number": round_number,
                    "tool_count": len(response.tool_calls),
                    "tool_names": [tool_call.name for tool_call in response.tool_calls],
                },
            )
            tool_calls = self._resolve_tool_calls(prepared, response.tool_calls)
            round_results = await self._tool_orchestrator.execute_all(
                tool_calls,
                agents=prepared.agents,
                runner=self,
            )
            tool_results.extend(round_results)

        content = response.content if response else None
        content = content or "I couldn't generate a response."
        result = AgentRunResult(
            content=content,
            tool_rounds=tool_rounds,
            tool_results=tool_results,
        )
        return result

    def _prepare_tools(self, tools: list[ToolDefinition | Agent]) -> PreparedTools:
        """Normalize tools and index schemas and sub-agents by provider-facing name."""
        definitions: dict[str, ToolDefinition] = {}
        agents: dict[str, Agent] = {}
        for tool in tools:
            if isinstance(tool, Agent):
                definition = self.agent_to_tool_definition(tool)
                agents[definition.name_formatted] = tool
            else:
                definition = tool
            definitions[definition.name_formatted] = definition
        prepared = PreparedTools(definitions=definitions, agents=agents)
        return prepared

    def _resolve_tool_calls(
        self,
        prepared: PreparedTools,
        tool_calls: list[ToolCall],
    ) -> list[ToolCall]:
        """Match LLM tool calls to definitions and normalize executor routing names."""
        resolved: list[ToolCall] = []
        for tool_call in tool_calls:
            definition = prepared.definitions.get(tool_call.name)
            if definition is None:
                resolved.append(tool_call)
                continue
            tool_key = tool_call.name if isinstance(definition, AgentToolDefinition) else None
            resolved.append(
                ToolCall(
                    id=tool_call.id,
                    name=definition.name.value,
                    arguments=tool_call.arguments,
                    tool_key=tool_key,
                )
            )
        return resolved

    @staticmethod
    def agent_to_tool_definition(agent: Agent) -> AgentToolDefinition:
        """Serialize an agent into a schema-only tool definition for a parent agent."""
        from agents.tools.agent_tool import AgentToolInput

        description = agent.agent_description or f"Run the {agent.name} agent."
        tool_definition = AgentToolDefinition(
            name=ToolName.AGENT_AS_TOOL,
            description=description,
            params_model=AgentToolInput,
            agent_name=format_agent_name(agent.name),
        )
        return tool_definition
