import uuid

from agents.client.openai_client import OpenAIClient
from agents.prompts.prompts import WeddingPromptJinja
from agents.prompts.types import LLMPromptInput
from services.types import Message
from services.wedding_service import WeddingService
from services.types import MessageRole


class WeddingAgent:
    """Run wedding planning chat sessions with the LLM."""

    def __init__(
        self,
        wedding_service: WeddingService,
        client: OpenAIClient | None = None,
    ):
        self._wedding_service = wedding_service
        self._client = client

    @staticmethod
    def default() -> "WeddingAgent":
        """Get the default wedding agent."""
        wedding_service = WeddingService.default()
        client = OpenAIClient.default()
        return WeddingAgent(wedding_service=wedding_service, client=client)

    def chat(
        self, query: str, session_id: uuid.UUID, max_tokens: int = 1024) -> Message:
        """Chat with the wedding agent."""
        prompt = WeddingPromptJinja(query=query)
        rendered_prompt = prompt.render()
         
        self._wedding_service.record_message(
            session_id=session_id,
            message_role=MessageRole.USER,
            message_content=query,
        )
        response = self._client.invoke(
            input=rendered_prompt,
            max_tokens=max_tokens,
        )

        self._wedding_service.record_message(
            session_id=session_id,
            message_role=MessageRole.ASSISTANT,
            message_content=response.text,
        )

        return response
