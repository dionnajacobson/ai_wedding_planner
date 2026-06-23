import uuid

from agents.client import LLMClient
from agents.client.types import LLMRequest, Model
from agents.prompts.prompts import WeddingPromptJinja
from agents.tools.registry import ToolRegistry
from services.message_service import MessageService
from services.types import Message, MessageRole
from services.wedding_service import WeddingService


class WeddingAgent:
    """Run wedding planning chat sessions with the LLM."""

    def __init__(
        self,
        client: LLMClient,
        message_service: MessageService,
        wedding_service: WeddingService,
        *,
        model: Model,
        tools: ToolRegistry,
    ):
        """Initialize the wedding agent."""
        self._client = client
        self._message_service = message_service
        self._wedding_service = wedding_service
        self._model = model
        self._tools = tools

    @staticmethod
    def default() -> "WeddingAgent":
        """Get the default wedding agent."""
        agent = WeddingAgent(
            client=LLMClient(),
            message_service=MessageService.default(),
            wedding_service=WeddingService.default(),
            model=Model.GPT_4O_MINI_2024_07_18,
            tools=ToolRegistry(),
        )
        return agent

    def chat(
        self,
        query: str,
        session_id: uuid.UUID,
        max_tokens: int = 1024,
    ) -> Message:
        """Chat with the wedding agent."""
        messages = self._message_service.get_messages(session_id)
        prompt = WeddingPromptJinja(messages=messages, query=query)
        rendered_prompt = prompt.render()

        request = LLMRequest(
            system=rendered_prompt.system,
            user=rendered_prompt.user,
            model=self._model,
            tools=self._tools.definitions(),
            max_tokens=max_tokens,
        )

        response = self._client.invoke(request=request)

        if response.tool_calls:
            tool_results = self._tools.execute_all(response.tool_calls)
            results_text = "\n".join(
                f"{result.tool_call_id}: {result.content}" for result in tool_results
            )
            follow_up = LLMRequest(
                system=rendered_prompt.system,
                user=f"{rendered_prompt.user}\n\nTool results:\n{results_text}",
                model=self._model,
                tools=self._tools.definitions(),
                max_tokens=max_tokens,
            )
            response = self._client.invoke(follow_up)

        content = response.content or "I couldn't generate a response."

        self._message_service.create_message(
            session_id,
            message_content=query,
            message_role=MessageRole.USER,
        )
        message = self._message_service.create_message(
            session_id,
            message_content=content,
            message_role=MessageRole.ASSISTANT,
        )
        return message
