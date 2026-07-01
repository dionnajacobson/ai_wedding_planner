"""Anthropic adapter for normalized LLM requests and responses."""

from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock
from openai.lib._pydantic import to_strict_json_schema

from agents.client.anthropic.types import AnthropicMessage, AnthropicPayload
from agents.client.errors import map_anthropic_error
from agents.client.protocols import LLMAdapter
from agents.client.types import LLMRequest, LLMResponse
from agents.tools.types import ToolCall, ToolDefinition


class AnthropicAdapter(LLMAdapter):
    """Translate normalized LLM payloads to and from the Anthropic Messages API."""

    def __init__(self, client: Anthropic | None = None) -> None:
        """Initialize the Anthropic adapter."""
        self._client = client or Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def invoke(self, request: LLMRequest) -> LLMResponse:
        """Format, call, and parse a normalized request."""
        payload = self._format_request(request)
        try:
            raw = self._call_api(payload)
        except Exception as exc:
            raise map_anthropic_error(exc) from exc
        response = self._parse_response(request, raw)
        return response

    def _format_request(self, request: LLMRequest) -> AnthropicPayload:
        """Convert a normalized request into a Messages API payload."""
        tools = None
        if request.tools:
            tools = [self._format_tool(tool) for tool in request.tools]

        _, model_id = request.model.value.split("/", maxsplit=1)
        payload = AnthropicPayload(
            model=model_id,
            max_tokens=request.max_tokens,
            system=request.system,
            messages=[AnthropicMessage(role="user", content=request.user)],
            tools=tools,
        )
        return payload

    def _call_api(self, payload: AnthropicPayload) -> Message:
        """Invoke the Anthropic Messages API."""
        response = self._client.messages.create(**payload.model_dump(exclude_none=True))
        return response

    def _parse_response(self, request: LLMRequest, raw: Message) -> LLMResponse:
        """Convert a Messages API result into a normalized response."""
        content_parts: list[str] = []
        for block in raw.content:
            if isinstance(block, TextBlock):
                content_parts.append(block.text)

        content = "".join(content_parts) or None
        response = LLMResponse(
            content=content,
            model=request.model,
            tool_calls=self._parse_tool_calls(raw),
        )
        return response

    def _format_tool(self, tool: ToolDefinition) -> dict[str, Any]:
        """Convert one tool definition into an Anthropic tool payload."""
        if tool.params_schema is not None:
            input_schema = tool.params_schema
        else:
            input_schema = to_strict_json_schema(tool.params_model)
        tool_payload = {
            "name": tool.provider_name,
            "description": tool.description,
            "input_schema": input_schema,
        }
        return tool_payload

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

        parsed_tool_calls = tool_calls or None
        return parsed_tool_calls
