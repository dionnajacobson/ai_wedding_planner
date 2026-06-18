from anthropic import Anthropic
from agents.client.base import LLMResponse, LLMClient
from agents.prompts.types import LLMPromptInput
import os
from dotenv import load_dotenv


load_dotenv(override=True)

class AnthropicClient(LLMClient):
    """Anthropic messages API client."""

    def __init__(self, model: str = "claude-sonnet-4-6", client: Anthropic | None = None):
        """Initialize the Anthropic client."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = client or Anthropic(api_key=self.api_key)

    def complete(
        self,
        *,
        input: LLMPromptInput,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a system prompt and user message; return the assistant reply."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=input.system,
            messages=[{"role": "user", "content": input.user}],
        )
        content = [block.text for block in response.content if block.type == "text"]
        text = "".join(content)
        response = LLMResponse(text=text, model=self.model, provider="anthropic")
        return response
