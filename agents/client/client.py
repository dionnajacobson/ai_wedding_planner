"""LLM client that routes requests to provider adapters."""

from agents.client.anthropic.adapter import AnthropicAdapter
from agents.client.openai.adapter import OpenAIAdapter
from agents.client.protocols import LLMAdapter
from agents.client.types import LLMRequest, LLMResponse


class LLMClient:
    """LLM client."""

    def _get_adapter(self, provider_name: str) -> LLMAdapter:
        """Get the adapter for a provider."""
        if provider_name == "openai":
            return OpenAIAdapter()
        if provider_name == "anthropic":
            return AnthropicAdapter()
        raise ValueError(f"Invalid provider: {provider_name}")

    def invoke(self, request: LLMRequest) -> LLMResponse:
        """Invoke the LLM client."""
        adapter = self._get_adapter(request.model.provider_name())
        formatted_request = adapter.format_request(request)
        invoke_response = adapter.invoke(formatted_request)
        return adapter.parse_response(invoke_response)
