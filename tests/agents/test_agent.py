"""Unit tests for the agent runner."""

from __future__ import annotations

import asyncio
from typing import Any

from agents.agent import Agent, AgentRunner
from agents.client.types import LLMRequest, LLMResponse, Model
from agents.prompts.base import JinjaPrompt
from agents.tools.registry import ToolRegistry
from agents.tools.types import ToolCall, ToolName
from tests.agents.mock_data import DaysUntilDateDefinition, DaysUntilDateExecutor


class MockLLMClient:
    """Return a scripted sequence of LLM responses."""

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = iter(responses)
        self.requests: list[LLMRequest] = []

    def invoke(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        response = next(self._responses)
        return response


class TestAgentRunner:
    """Table-driven tests for AgentRunner."""

    def test_run(self) -> None:
        """Run agent runner scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "executes_tools_until_final_answer",
                "llm_responses": [
                    LLMResponse(
                        content=None,
                        model=Model.GPT_4O_MINI_2024_07_18,
                        tool_calls=[
                            ToolCall(
                                id="call_1",
                                name="days_until_date",
                                arguments={"event_date": "2099-01-01"},
                            )
                        ],
                    ),
                    LLMResponse(
                        content="Your wedding is far away.",
                        model=Model.GPT_4O_MINI_2024_07_18,
                        tool_calls=None,
                    ),
                ],
                "expected_content": "Your wedding is far away.",
                "expected_tool_rounds": 1,
                "expected_tool_result_count": 1,
                "expected_tool_result_counts": [0, 1],
                "expected_request_count": 2,
                "expected_tool_name": ToolName.DAYS_UNTIL_DATE,
            },
        ]

        for case in test_cases:
            # ARRANGE
            registry = ToolRegistry()
            registry.register(ToolName.DAYS_UNTIL_DATE, DaysUntilDateExecutor())
            prompt = _TestPrompt()
            agent = Agent(
                name="Planner",
                model=Model.GPT_4O_MINI_2024_07_18,
                tools=[DaysUntilDateDefinition()],
                prompt=prompt,
            )
            client = MockLLMClient(case["llm_responses"])
            runner = AgentRunner(client, registry)

            # ACT
            result = asyncio.run(runner.run(agent))

            # ASSERT
            assert result.content == case["expected_content"]
            assert result.tool_rounds == case["expected_tool_rounds"]
            assert len(result.tool_results) == case["expected_tool_result_count"]
            assert prompt.tool_result_counts == case["expected_tool_result_counts"]
            assert len(client.requests) == case["expected_request_count"]
            assert client.requests[0].tools is not None
            assert client.requests[0].tools[0].name == case["expected_tool_name"]


class _TestPrompt(JinjaPrompt):
    """Minimal Jinja prompt for runner tests."""

    template_name = "base.jinja"

    def __init__(self) -> None:
        super().__init__(user_context={"note": "static"})
        self.tool_result_counts: list[int] = []

    def update_context(self, **context) -> None:
        tool_results = context.get("tool_results")
        if tool_results is not None:
            self.tool_result_counts.append(len(tool_results))
        super().update_context(**context)
