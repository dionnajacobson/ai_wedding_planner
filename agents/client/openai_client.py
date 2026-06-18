from openai import OpenAI
from agents.client.base import LLMResponse, LLMClient
from agents.prompts.types import LLMPromptInput
import os
from dotenv import load_dotenv


load_dotenv(override=True)


class OpenAIClient(LLMClient):
    """OpenAI chat completions client."""

    def __init__(self, model: str = "gpt-4.1-mini", client: OpenAI | None = None):
        """Initialize the OpenAI client."""
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = client or OpenAI(api_key=self.api_key)

    def complete(
        self,
        *,
        input: LLMPromptInput,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a system prompt and user message; return the assistant reply."""
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": input.system},
                {"role": "user", "content": input.user},
            ],
        )
        text = response.choices[0].message.content or ""
        response = LLMResponse(text=text, model=self.model, provider="openai")
        return response
