import logging
import uuid

from fastapi import APIRouter, HTTPException

from agents.client.errors import LLMAuthError, LLMError, LLMRateLimitError
from agents.wedding_agent import WeddingAgent
from api.schemas import (
    ChatRequest,
    ChatResponse,
    MessagesResponse,
    StartChatRequest,
    StartChatResponse,
)
from services.message_service import MessageService
from services.wedding_service import WeddingService

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/api/chat/start", response_model=StartChatResponse, status_code=201)
def start_chat(body: StartChatRequest) -> StartChatResponse:
    """Create a client, wedding, and chat session."""
    wedding_service = WeddingService.default()
    client = wedding_service.onboard_client(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    session_id = wedding_service.create_session(client_id=client.id)
    logger.info(
        "chat_session_started",
        extra={"session_id": str(session_id), "client_id": str(client.id)},
    )
    response = StartChatResponse(session_id=session_id)
    return response


@router.post("/api/chat", response_model=ChatResponse)
async def send_message(body: ChatRequest) -> ChatResponse:
    """Send a message and receive the assistant reply."""
    agent = WeddingAgent.default()
    try:
        message = await agent.chat(
            query=body.message,
            session_id=body.session_id,
        )
    except ValueError as exc:
        if "Wedding not found" in str(exc):
            logger.warning("chat_wedding_not_found", extra={"error": str(exc)})
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        logger.exception("chat_value_error", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except LLMAuthError as exc:
        logger.warning("chat_llm_auth_error", extra={"error": str(exc)})
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except LLMRateLimitError as exc:
        logger.warning("chat_llm_rate_limit", extra={"error": str(exc)})
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except LLMError as exc:
        logger.error("chat_llm_error", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response = ChatResponse(session_id=body.session_id, message=message)
    return response


@router.get("/api/chat/{session_id}/messages", response_model=MessagesResponse)
def get_messages(session_id: uuid.UUID) -> MessagesResponse:
    """Return the conversation history for a session."""
    message_service = MessageService.default()
    messages = message_service.get_messages(session_id)
    response = MessagesResponse(session_id=session_id, messages=messages)
    return response
