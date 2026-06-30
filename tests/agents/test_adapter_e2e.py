import os
from typing import Any

import pytest
from dotenv import load_dotenv

from agents.client.anthropic.adapter import AnthropicAdapter
from agents.client.openai.adapter import OpenAIAdapter
from agents.client.types import LLMRequest, Model
from tests.agents.mock_data import DaysUntilDateDefinition

load_dotenv()


@pytest.mark.api
class TestAdapterE2E:
    """End-to-end table-driven tests for provider adapters."""

    adapter_cases = [
        pytest.param(
            OpenAIAdapter,
            Model.GPT_4O_MINI_2024_07_18,
            "OPENAI_API_KEY",
            id="openai",
        ),
        pytest.param(
            AnthropicAdapter,
            Model.CLAUDE_SONNET_4_6,
            "ANTHROPIC_API_KEY",
            id="anthropic",
        ),
    ]

    e2e_test_cases: list[dict[str, Any]] = [
        {
            "name": "returns_text_for_simple_prompt",
            "system": "You are a concise wedding planning assistant.",
            "user": "Reply with exactly: Hello from the planner.",
            "tools": None,
            "expect_tool_calls": False,
            "content_contains": "Hello",
        },
        {
            "name": "returns_tool_call_for_date_question",
            "system": (
                "You are a wedding planning assistant. "
                "Always use the days_until_date tool for date countdown questions."
            ),
            "user": "How many days until 2026-09-15?",
            "tools": [DaysUntilDateDefinition()],
            "expect_tool_calls": True,
            "expected_tool_name": "days_until_date",
            "expected_argument_key": "event_date",
        },
    ]

    @pytest.mark.parametrize("adapter_cls,model,api_key_env", adapter_cases)
    def test_adapter_e2e(
        self,
        adapter_cls: type[OpenAIAdapter] | type[AnthropicAdapter],
        model: Model,
        api_key_env: str,
    ) -> None:
        """Run adapter scenarios from the shared test table."""
        if not os.getenv(api_key_env):
            pytest.skip(f"{api_key_env} not set")

        adapter = adapter_cls()

        for case in self.e2e_test_cases:
            # ARRANGE
            request = LLMRequest(
                system=case["system"],
                user=case["user"],
                model=model,
                tools=case["tools"],
            )

            # ACT
            response = adapter.invoke(request)

            # ASSERT
            assert response.model == model

            if case["expect_tool_calls"]:
                assert response.tool_calls
                assert len(response.tool_calls) >= 1
                assert response.tool_calls[0].name == case["expected_tool_name"]
                assert case["expected_argument_key"] in response.tool_calls[0].arguments
            else:
                assert response.tool_calls is None
                assert response.content
                assert case["content_contains"] in response.content
