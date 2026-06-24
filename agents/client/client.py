"""LLM client that routes requests to provider adapters."""

from __future__ import annotations

import logging
import time

from agents.client.anthropic.adapter import AnthropicAdapter
from agents.client.openai.adapter import OpenAIAdapter
from agents.client.protocols import LLMAdapter
from agents.client.types import LLMRequest, LLMResponse, Provider

logger = logging.getLogger(__name__)


def default_adapters() -> dict[Provider, LLMAdapter]:
    """Build the default provider adapter registry."""
    adapters = {
        Provider.OPENAI: OpenAIAdapter(),
        Provider.ANTHROPIC: AnthropicAdapter(),
    }
    return adapters


class LLMClient:
    """Route normalized requests to injected provider adapters."""

    def __init__(self, adapters: dict[Provider, LLMAdapter]) -> None:
        """Initialize the LLM client with a provider adapter registry."""
        self._adapters = adapters

    @staticmethod
    def default() -> LLMClient:
        """Get the default LLM client."""
        return LLMClient(adapters=default_adapters())

    def invoke(self, request: LLMRequest) -> LLMResponse:
        """Invoke the adapter for the request model's provider."""
        provider_name, _ = request.model.value.split("/", maxsplit=1)
        provider = Provider(provider_name)
        adapter = self._adapters.get(provider)
        if adapter is None:
            raise ValueError(f"Invalid provider: {provider}")

        start = time.perf_counter()
        response = adapter.invoke(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "llm_invoke_completed",
            extra={
                "provider": provider.value,
                "model": request.model.value,
                "duration_ms": duration_ms,
                "has_tool_calls": bool(response.tool_calls),
            },
        )
        return response
