"""Unit tests for JinjaPrompt runtime context."""

from __future__ import annotations

from agents.prompts.base import JinjaPrompt
from agents.prompts.prompts import WeddingPromptJinja
from agents.tools.types import ToolResult
from services.types import MessageRole
from tests.services.mock_data import mock_message


class TestJinjaPromptRuntimeContext:
    """Table-driven tests for runtime context handling."""

    def test_update_context_uses_registered_formatter(self) -> None:
        """Format runtime values through the subclass runtime_fields registry."""
        prompt = WeddingPromptJinja(
            query="What are venue costs?",
            messages=[mock_message(content="Hello", role=MessageRole.USER)],
        )
        tool_results = [
            ToolResult(tool_call_id="call_1", content="Average cost is $8,000."),
        ]

        prompt.update_context(tool_results=tool_results)
        rendered = prompt.render()

        assert "<tool_results>" in rendered.user
        assert "$8,000" in rendered.user

    def test_unknown_runtime_keys_are_stringified(self) -> None:
        """Store unregistered runtime keys as plain strings."""

        class DebugPrompt(JinjaPrompt):
            template_name = "base.jinja"

        prompt = DebugPrompt(user_context={"note": "static"})
        prompt.update_context(debug_count=3)

        assert prompt.runtime_context["debug_count"] == "3"
