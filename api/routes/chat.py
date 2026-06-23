import uuid

from fastapi import APIRouter, HTTPException

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
    return StartChatResponse(session_id=session_id)


@router.post("/api/chat", response_model=ChatResponse)
def send_message(body: ChatRequest) -> ChatResponse:
    """Send a message and receive the assistant reply."""
    agent = WeddingAgent.default()
    try:
        message = agent.chat(
            query=body.message,
            session_id=body.session_id,
            max_tokens=body.max_tokens,
        )
    except ValueError as exc:
        if "Wedding not found" in str(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(session_id=body.session_id, message=message)


@router.get("/api/chat/{session_id}/messages", response_model=MessagesResponse)
def get_messages(session_id: uuid.UUID) -> MessagesResponse:
    """Return the conversation history for a session."""
    message_service = MessageService.default()
    messages = message_service.get_messages(session_id)
    return MessagesResponse(session_id=session_id, messages=messages)
