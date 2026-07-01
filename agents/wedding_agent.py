import logging
import uuid

from agents.agent import Agent, AgentRunner
from agents.client.types import Model
from agents.prompts.prompts import VendorSearchPromptJinja, WeddingPromptJinja
from agents.tools.tools.save_vendor import SaveVendorDefinition
from agents.tools.tools.servers import ApifyMcpServer
from observability.logging import log_context
from services.message_service import MessageService
from services.types import Message, MessageRole
from services.wedding_service import WeddingService

logger = logging.getLogger(__name__)


class WeddingAgent:
    """Run wedding planning chat sessions with the LLM."""

    def __init__(
        self,
        message_service: MessageService,
        runner: AgentRunner,
        wedding_service: WeddingService,
    ):
        """Initialize the wedding agent."""
        self._message_service = message_service
        self._runner = runner
        self._wedding_service = wedding_service

    async def chat(
        self,
        query: str,
        session_id: uuid.UUID,
    ) -> Message:
        """Chat with the wedding agent."""
        with log_context(session_id=str(session_id)):
            logger.info("chat_started")

            history = self._message_service.get_messages(session_id)
            prompt = WeddingPromptJinja(query=query, history=history)
            vendor_agent = Agent(
                name="vendor_search",
                agent_description="Helps find vendors for the wedding.",
                model=Model.GPT_4O_MINI_2024_07_18,
                tools=[ApifyMcpServer, SaveVendorDefinition(session_id=session_id)],
                prompt=VendorSearchPromptJinja(query=query, history=history),
            )
            agent = Agent(
                name="wedding_planner",
                model=Model.GPT_4O_MINI_2024_07_18,
                tools=[vendor_agent],
                prompt=prompt,
            )
            result = await self._runner.run(agent)

            self._message_service.create_message(
                session_id,
                message_content=query,
                message_role=MessageRole.USER,
            )
            message = self._message_service.create_message(
                session_id,
                message_content=result.content,
                message_role=MessageRole.ASSISTANT,
            )

            logger.info(
                "chat_completed",
                extra={
                    "tool_rounds": result.tool_rounds,
                    "response_length": len(result.content),
                },
            )
            return message
