from typing import Protocol, runtime_checkable
from pydantic import BaseModel
from agents.prompts.types import LLMPromptInput


class LLMResponse(BaseModel):
    """Normalized response from any LLM provider."""

    text: str
    model: str
    provider: str


@runtime_checkable
class LLMClient(Protocol):
    """Call different LLM providers with the same interface."""

    def invoke(
        self,
        *,
        input: LLMPromptInput,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a system prompt and user message; return the assistant reply."""
        ...
