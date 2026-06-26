"""Unit tests for agent-as-tool execution."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import Mock, patch

from agents.agent import Agent, AgentRunResult
from agents.client.types import Model
from agents.prompts.base import JinjaPrompt
from agents.tools.agent_tool import AgentToolExecutor
from agents.tools.orchestrator import ToolOrchestrator
from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolName, format_agent_name


class _TaskPrompt(JinjaPrompt):
    template_name = "base.jinja"


class _RecordingRunner:
    """Capture the agent passed to run() and return a fixed reply."""

    def __init__(self, content: str = "Sub-agent reply") -> None:
        self.content = content
        self.agents: list[Agent] = []
        self._orchestrator = ToolOrchestrator(
            executors={ToolName.AGENT_AS_TOOL: AgentToolExecutor(runner=self)},
        )

    async def run(self, agent: Agent) -> AgentRunResult:
        self.agents.append(agent)
        result = AgentRunResult(content=self.content)
        return result


class TestAgentAsTool:
    """Table-driven tests for agent-as-tool execution through the orchestrator."""

    def test_default_orchestrator_executes_agent_tool(self) -> None:
        """Run agent-as-tool execution scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "routes_provider_facing_name_to_sub_agent",
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
                name=f"agent_as_tool_{format_agent_name(sub_agent.name)}",
                arguments=case["tool_call"].arguments,
            )
            orchestrator = runner._orchestrator
            entries = orchestrator.prepare([sub_agent])

            # ACT
            result = asyncio.run(
                orchestrator.execute_all(
                    [tool_call],
                    entries=entries,
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
