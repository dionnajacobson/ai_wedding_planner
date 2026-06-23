"""OpenAI adapter for normalized LLM requests and responses."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from openai.lib._pydantic import to_strict_json_schema
from openai.types.responses import Response

from agents.client.openai.types import OpenAIPayload
from agents.client.protocols import LLMAdapter
from agents.client.types import LLMRequest, LLMResponse
from agents.tools.types import ToolCall, ToolDefinition


class OpenAIAdapter(LLMAdapter):
    """Translate normalized LLM payloads to and from the OpenAI Responses API."""

    def __init__(self):
        """Initialize the OpenAI adapter."""
        key = os.getenv("OPENAI_API_KEY")
        self._client = OpenAI(api_key=key)

    def invoke(self, request: OpenAIPayload) -> Response:
        """Invoke the OpenAI Responses API."""
        payload = request.model_dump(exclude_none=True)
        response = self._client.responses.create(**payload)
        return response

    def format_request(self, request: LLMRequest) -> OpenAIPayload:
        """Convert a normalized request into a Responses API payload."""
        tools = None
        if request.tools:
            tools = [self._format_tool(tool) for tool in request.tools]

        payload = OpenAIPayload(
            model=request.model.model_name(),
            input=request.user,
            instructions=request.system,
            tools=tools,
        )
        return payload

    def parse_response(self, raw: Response) -> LLMResponse:
        """Convert a Responses API result into a normalized response."""
        response = LLMResponse(
            content=raw.output_text,
            model=raw.model,
            tool_calls=self._parse_tool_calls(raw),
        )
        return response

    def _format_tool(self, tool: ToolDefinition) -> dict[str, Any]:
        """Convert one tool definition into a Responses API function tool."""
        tool_payload = {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": to_strict_json_schema(tool.params_model),
            "strict": True,
        }
        return tool_payload

    def _parse_tool_calls(self, response: Response) -> list[ToolCall] | None:
        """Parse function_call items from the response output array."""
        tool_calls: list[ToolCall] = []
        for item in response.output:
            if item.type != "function_call":
                continue
            arguments = json.loads(item.arguments or "{}")
            tool_calls.append(
                ToolCall(
                    id=item.call_id,
                    name=item.name,
                    arguments=arguments,
                )
            )

        tool_calls = tool_calls or None
        return tool_calls
