import os
from typing import Any

import pytest
from dotenv import load_dotenv

from agents.client.openai.adapter import OpenAIAdapter
from agents.client.types import LLMRequest, Model
from tests.agents.mock_data import mock_days_until_date_tool

load_dotenv()


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestOpenAIAdapter:
    """End-to-end table-driven tests for OpenAIAdapter against the Responses API."""

    def test_adapter_e2e(self) -> None:
        """Run adapter scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_text_for_simple_prompt",
                "system": "You are a concise wedding planning assistant.",
                "user": "Reply with exactly: Hello from the planner.",
                "model": Model.GPT_4O_MINI_2024_07_18,
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
                "model": Model.GPT_4O_MINI_2024_07_18,
                "tools": [mock_days_until_date_tool()],
                "expect_tool_calls": True,
                "expected_tool_name": "days_until_date",
                "expected_argument_key": "event_date",
            },
        ]

        adapter = OpenAIAdapter()

        for case in test_cases:
            # ARRANGE
            request = LLMRequest(
                system=case["system"],
                user=case["user"],
                model=case["model"],
                tools=case["tools"],
            )

            # ACT
            payload = adapter.format_request(request)
            raw = adapter.invoke(payload)
            response = adapter.parse_response(raw)

            # ASSERT
            assert response.model == case["model"].model_name()
            assert raw.id
            assert raw.output

            if case["expect_tool_calls"]:
                assert response.tool_calls
                assert len(response.tool_calls) >= 1
                assert response.tool_calls[0].name == case["expected_tool_name"]
                assert case["expected_argument_key"] in response.tool_calls[0].arguments
            else:
                assert response.tool_calls is None
                assert response.content
                assert case["content_contains"] in response.content
