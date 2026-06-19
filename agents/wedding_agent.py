import uuid

from agents.client.openai_client import OpenAIClient
from agents.prompts.prompts import WeddingPromptJinja
from services.message_service import MessageService
from services.types import Message, MessageRole
from services.wedding_service import WeddingService


class WeddingAgent:
    """Run wedding planning chat sessions with the LLM."""

    def __init__(
        self,
        client: OpenAIClient | None,
        message_service: MessageService,
        wedding_service: WeddingService,
    ):
        """Initialize the wedding agent."""
        self._client = client
        self._message_service = message_service
        self._wedding_service = wedding_service

    @staticmethod
    def default() -> "WeddingAgent":
        """Get the default wedding agent."""
        client = OpenAIClient()
        message_service = MessageService.default()
        wedding_service = WeddingService.default()
        agent = WeddingAgent(
            client=client,
            message_service=message_service,
            wedding_service=wedding_service,
        )
        return agent

    def chat(
        self,
        query: str,
        session_id: uuid.UUID,
        max_tokens: int = 1024,
    ) -> Message:
        """Chat with the wedding agent."""
        prompt = WeddingPromptJinja(query=query)
        rendered_prompt = prompt.render()

        self._message_service.create_message(
            session_id,
            message_content=query,
            message_role=MessageRole.USER,
        )
        response = self._client.invoke(
            input=rendered_prompt,
            max_tokens=max_tokens,
        )
        message = self._message_service.create_message(
            session_id,
            message_content=response.text,
            message_role=MessageRole.ASSISTANT,
        )
        return message
