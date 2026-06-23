"""Protocols for LLM clients and provider adapters."""

from typing import Protocol, runtime_checkable

from agents.client.types import LLMRequest, LLMResponse


@runtime_checkable
class LLMAdapter(Protocol):
    """Translate between normalized requests/responses and a provider API."""

    def invoke(self, request: LLMRequest) -> LLMResponse:
        """Format, call, and parse a normalized LLM request."""
        ...
