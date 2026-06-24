"""OpenAI adapter for normalized LLM requests and responses."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from openai.lib._pydantic import to_strict_json_schema
from openai.types.responses import Response

from agents.client.errors import map_openai_error
from agents.client.openai.types import OpenAIPayload
from agents.client.protocols import LLMAdapter
from agents.client.types import LLMRequest, LLMResponse
from agents.tools.types import ToolCall, ToolDefinition


class OpenAIAdapter(LLMAdapter):
    """Translate normalized LLM payloads to and from the OpenAI Responses API."""

    def __init__(self, client: OpenAI | None = None) -> None:
        """Initialize the OpenAI adapter."""
        self._client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def invoke(self, request: LLMRequest) -> LLMResponse:
        """Format, call, and parse a normalized request."""
        payload = self._format_request(request)
        try:
            raw = self._call_api(payload)
        except Exception as exc:
            raise map_openai_error(exc) from exc
        response = self._parse_response(request, raw)
        return response

    def _format_request(self, request: LLMRequest) -> OpenAIPayload:
        """Convert a normalized request into a Responses API payload."""
        tools = None
        if request.tools:
            tools = [self._format_tool(tool) for tool in request.tools]

        _, model_id = request.model.value.split("/", maxsplit=1)
        payload = OpenAIPayload(
            model=model_id,
            input=request.user,
            instructions=request.system,
            max_output_tokens=request.max_tokens,
            tools=tools,
        )
        return payload

    def _call_api(self, payload: OpenAIPayload) -> Response:
        """Invoke the OpenAI Responses API."""
        response = self._client.responses.create(**payload.model_dump(exclude_none=True))
        return response

    def _parse_response(self, request: LLMRequest, raw: Response) -> LLMResponse:
        """Convert a Responses API result into a normalized response."""
        response = LLMResponse(
            content=raw.output_text,
            model=request.model,
            tool_calls=self._parse_tool_calls(raw),
        )
        return response

    def _format_tool(self, tool: ToolDefinition) -> dict[str, Any]:
        """Convert one tool definition into a Responses API function tool."""
        tool_payload = {
            "type": "function",
            "name": tool.name.value,
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

        parsed_tool_calls = tool_calls or None
        return parsed_tool_calls
