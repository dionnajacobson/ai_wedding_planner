"""Anthropic adapter for normalized LLM requests and responses."""

from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock

from agents.client.anthropic.types import AnthropicMessage, AnthropicPayload
from agents.client.protocols import LLMAdapter
from agents.client.types import LLMRequest, LLMResponse
from agents.tools.types import ToolCall, ToolDefinition


class AnthropicAdapter(LLMAdapter):
    """Translate normalized LLM payloads to and from the Anthropic Messages API."""

    def __init__(self):
        """Initialize the Anthropic adapter."""
        key = os.getenv("ANTHROPIC_API_KEY")
        self._client = Anthropic(api_key=key)

    def invoke(self, request: AnthropicPayload) -> Message:
        """Invoke the Anthropic Messages API."""
        payload = request.model_dump(exclude_none=True)
        return self._client.messages.create(**payload)

    def format_request(self, request: LLMRequest) -> AnthropicPayload:
        """Convert a normalized request into a Messages API payload."""
        tools = None
        if request.tools:
            tools = [self._format_tool(tool) for tool in request.tools]

        return AnthropicPayload(
            model=request.model.model_name(),
            max_tokens=request.max_tokens,
            system=request.system,
            messages=[AnthropicMessage(role="user", content=request.user)],
            tools=tools,
        )

    def parse_response(self, raw: Message) -> LLMResponse:
        """Convert a Messages API result into a normalized response."""
        content_parts: list[str] = []
        for block in raw.content:
            if isinstance(block, TextBlock):
                content_parts.append(block.text)

        return LLMResponse(
            content="".join(content_parts) or None,
            model=raw.model,
            tool_calls=self._parse_tool_calls(raw),
        )

    def _format_tool(self, tool: ToolDefinition) -> dict[str, Any]:
        """Convert one tool definition into an Anthropic tool payload."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.params_model.model_json_schema(),
        }

    def _parse_tool_calls(self, response: Message) -> list[ToolCall] | None:
        """Parse tool_use blocks from the response content."""
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if not isinstance(block, ToolUseBlock):
                continue
            tool_calls.append(
                ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=dict(block.input),
                )
            )

        return tool_calls or None
