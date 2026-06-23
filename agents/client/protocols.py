"""Protocols for LLM clients and provider adapters."""

from typing import Any, Protocol, runtime_checkable

from agents.client.types import LLMRequest, LLMResponse


@runtime_checkable
class LLMAdapter(Protocol):
    """Translate between normalized requests/responses and a provider API."""

    def format_request(self, request: LLMRequest) -> Any:
        """Convert a normalized request into a provider-specific payload."""
        ...

    def parse_response(self, raw: Any) -> LLMResponse:
        """Convert a provider-specific response into a normalized response."""
        ...

    def invoke(self, formatted_request: Any) -> Any:
        """Invoke the provider API."""
        ...
