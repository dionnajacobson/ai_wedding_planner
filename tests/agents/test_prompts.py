from typing import Any

from agents.prompts.prompts import BaseJinjaPrompt, WeddingPromptJinja
from agents.tools.types import ToolResult
from services.types import MessageRole
from tests.base import PromptDataAssertionTest
from tests.services.mock_data import mock_message


class TestBaseJinja(PromptDataAssertionTest):
    """Table-driven tests for the base Jinja prompt."""

    overwrite_test_data = False

    def test_base_jinja_e2e(self) -> None:
        """Run base prompt scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "renders_default_prompt",
                "prompt": BaseJinjaPrompt(),
                "fixture_name": "base_prompt",
            },
        ]

        for case in test_cases:
            # ACT
            rendered = case["prompt"].render()

            # ASSERT
            self.assert_test_data(rendered, case["fixture_name"])


class TestWeddingPromptJinja(PromptDataAssertionTest):
    """Table-driven tests for the wedding prompt."""

    overwrite_test_data = False

    def test_wedding_prompt_jinja_e2e(self) -> None:
        """Run wedding prompt scenarios from the test table."""
        mock_messages = [
            mock_message(
                content="We are getting married in 6 months and need to plan a wedding.",
                role=MessageRole.USER,
            ),
            mock_message(
                content="We need to book a venue, caterer, and photographer.",
                role=MessageRole.ASSISTANT,
            ),
        ]
        test_cases: list[dict[str, Any]] = [
            {
                "name": "renders_wedding_prompt_with_history",
                "prompt": WeddingPromptJinja(
                    query="What should we focus on next?",
                    messages=mock_messages,
                ),
                "fixture_name": "wedding_prompt",
            },
            {
                "name": "renders_wedding_prompt_with_tool_results",
                "prompt": WeddingPromptJinja(
                    query="What are average venue costs in Austin?",
                    messages=mock_messages,
                    tool_results=[
                        ToolResult(
                            tool_call_id="call_1",
                            content="Average Austin venue cost is $8,000.",
                        )
                    ],
                ),
                "fixture_name": "wedding_prompt_with_tool_results",
            },
        ]

        for case in test_cases:
            # ACT
            rendered = case["prompt"].render()

            # ASSERT
            self.assert_test_data(rendered, case["fixture_name"])
