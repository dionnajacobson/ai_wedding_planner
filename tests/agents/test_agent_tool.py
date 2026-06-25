"""Unit tests for agent-as-tool conversion."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import Mock, patch

from agents.agent import Agent, AgentRunner, AgentRunResult, AgentToolInput
from agents.client.types import Model
from agents.prompts.base import JinjaPrompt
from agents.tools.agent_tool import AgentToolExecutor
from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.protocols import ToolExecutor
from agents.tools.types import AgentToolDefinition, ToolCall, ToolName, format_agent_name


class _TaskPrompt(JinjaPrompt):
    template_name = "base.jinja"


class _RecordingRunner:
    """Capture the agent passed to run() and return a fixed reply."""

    def __init__(self, content: str = "Sub-agent reply") -> None:
        self.content = content
        self.agents: list[Agent] = []
        self._orchestrator = ToolOrchestrator(
            {ToolName.AGENT_AS_TOOL: AgentToolExecutor(runner=self)},
        )

    async def run(self, agent: Agent) -> AgentRunResult:
        self.agents.append(agent)
        result = AgentRunResult(content=self.content)
        return result


class _ToolRunner:
    """Minimal runner for prepare/resolve tests."""

    def __init__(self) -> None:
        self._orchestrator = ToolOrchestrator()


class _UnusedClient:
    """Placeholder client; prepare/resolve tests do not invoke the LLM."""


class TestAgentAsTool:
    """Table-driven tests for AgentRunner.agent_to_tool_definition() and AgentToolExecutor."""

    def test_agent_to_tool_definition_builds_definition(self) -> None:
        """Run definition-building scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "uses_agent_as_tool_name_and_description",
                "agent_kwargs": {
                    "name": "Researcher",
                    "agent_description": "Run the Researcher agent.",
                },
                "expected_name": ToolName.AGENT_AS_TOOL,
                "expected_description": "Run the Researcher agent.",
            },
            {
                "name": "defaults_description_from_agent_name",
                "agent_kwargs": {
                    "name": "Researcher",
                },
                "expected_name": ToolName.AGENT_AS_TOOL,
                "expected_description": "Run the Researcher agent.",
            },
        ]

        for case in test_cases:
            agent = Agent(
                model=Model.GPT_4O_MINI_2024_07_18,
                prompt=_TaskPrompt(),
                **case["agent_kwargs"],
            )

            definition = AgentRunner.agent_to_tool_definition(agent)

            assert isinstance(definition, AgentToolDefinition)
            assert definition.name == case["expected_name"]
            assert definition.description == case["expected_description"]
            assert definition.params_model is AgentToolInput
            assert definition.agent_name == format_agent_name(agent.name)
            assert definition.name_formatted == f"agent_as_tool.{format_agent_name(agent.name)}"

    def test_prepare_tools_converts_agents(self) -> None:
        """Sub-agents in tools are converted and indexed by name."""
        sub_agent = Agent(
            name="Researcher",
            model=Model.GPT_4O_MINI_2024_07_18,
            prompt=_TaskPrompt(),
        )
        runner = AgentRunner(client=_UnusedClient(), tool_orchestrator=ToolOrchestrator())

        prepared = runner._prepare_tools([sub_agent])
        tool_key = f"agent_as_tool.{format_agent_name(sub_agent.name)}"
        definition = prepared.definitions[tool_key]

        assert isinstance(definition, AgentToolDefinition)
        assert prepared.agents[tool_key] is sub_agent

    def test_default_orchestrator_executes_agent_tool(self) -> None:
        """Run agent-as-tool execution scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "applies_task_input_to_agent_prompt",
                "tool_call": ToolCall(
                    id="call_1",
                    name="agent_as_tool",
                    arguments={"task": "Find Austin venues"},
                ),
                "expected_tool_call_id": "call_1",
                "expected_content": "Sub-agent reply",
                "expected_sub_agent_name": "Researcher",
                "expected_prompt_context": {"task": "Find Austin venues"},
            },
        ]

        for case in test_cases:
            # ARRANGE
            runner = _RecordingRunner(content=case["expected_content"])
            sub_agent = Agent(
                name=case["expected_sub_agent_name"],
                model=Model.GPT_4O_MINI_2024_07_18,
                prompt=_TaskPrompt(),
            )
            tool_call = ToolCall(
                id=case["tool_call"].id,
                name=f"agent_as_tool.{format_agent_name(sub_agent.name)}",
                arguments=case["tool_call"].arguments,
            )
            tool_runner = AgentRunner(client=runner, tool_orchestrator=runner._orchestrator)
            prepared = tool_runner._prepare_tools([sub_agent])
            tool_call = tool_runner._resolve_tool_calls(prepared, [tool_call])[0]

            assert tool_call.name == ToolName.AGENT_AS_TOOL.value
            assert tool_call.tool_key == f"agent_as_tool.{format_agent_name(sub_agent.name)}"

            # ACT
            result = asyncio.run(
                runner._orchestrator.execute_all(
                    [tool_call],
                    agents=prepared.agents,
                    runner=runner,
                ),
            )[0]

            # ASSERT
            assert isinstance(
                runner._orchestrator._executors[ToolName.AGENT_AS_TOOL],
                ToolExecutor,
            )
            assert result.tool_call_id == case["expected_tool_call_id"]
            assert result.content == case["expected_content"]
            assert len(runner.agents) == 1
            assert runner.agents[0].name == case["expected_sub_agent_name"]
            assert runner.agents[0].prompt.runtime_context == case["expected_prompt_context"]

    def test_default_orchestrator_includes_standard_executors(self) -> None:
        """Default orchestrator includes web search and agent-as-tool executors."""
        with patch("agents.tools.orchestrator.WebSearchExecutor", return_value=Mock()):
            orchestrator = ToolOrchestrator.default()

        web_search = orchestrator._get_executor(ToolName.WEB_SEARCH)
        agent_tool = orchestrator._get_executor(ToolName.AGENT_AS_TOOL)

        assert web_search is not None
        assert isinstance(agent_tool, AgentToolExecutor)
