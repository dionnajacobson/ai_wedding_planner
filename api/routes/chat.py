import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.agent import AgentRunner
from agents.client.errors import LLMAuthError, LLMError, LLMRateLimitError
from agents.wedding_agent import WeddingAgent
from api.schemas import (
    ChatRequest,
    ChatResponse,
    MessagesResponse,
    StartChatRequest,
    StartChatResponse,
    WeddingResponse,
)
from db.database import get_db
from services.client_service import ClientService
from services.message_service import MessageService
from services.stores.client_store import ClientStore
from services.stores.message_store import MessageStore
from services.stores.wedding_store import WeddingStore
from services.wedding_service import WeddingService

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/api/chat/start", response_model=StartChatResponse, status_code=201)
def start_chat(body: StartChatRequest, db: Session = Depends(get_db)) -> StartChatResponse:
    """Create a client, wedding, and chat session."""
    client_store = ClientStore(db_session=db)
    wedding_store = WeddingStore(db_session=db, client_store=client_store)
    client_service = ClientService(store=client_store, wedding_store=wedding_store)
    wedding_service = WeddingService(client_service=client_service, wedding_store=wedding_store)

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
async def send_message(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Send a message and receive the assistant reply."""
    client_store = ClientStore(db_session=db)
    wedding_store = WeddingStore(db_session=db, client_store=client_store)
    client_service = ClientService(store=client_store, wedding_store=wedding_store)
    message_store = MessageStore(db_session=db)
    message_service = MessageService(store=message_store)
    wedding_service = WeddingService(client_service=client_service, wedding_store=wedding_store)
    agent = WeddingAgent(
        message_service=message_service,
        runner=AgentRunner.default(),
        wedding_service=wedding_service,
    )

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
def get_messages(session_id: uuid.UUID, db: Session = Depends(get_db)) -> MessagesResponse:
    """Return the conversation history for a session."""
    message_store = MessageStore(db_session=db)
    message_service = MessageService(store=message_store)
    messages = message_service.get_messages(session_id)
    response = MessagesResponse(messages=messages, session_id=session_id)
    return response


@router.get("/api/chat/{session_id}/wedding", response_model=WeddingResponse)
def get_wedding(session_id: uuid.UUID, db: Session = Depends(get_db)) -> WeddingResponse:
    """Return the wedding profile linked to a chat session."""
    client_store = ClientStore(db_session=db)
    wedding_store = WeddingStore(client_store=client_store, db_session=db)
    client_service = ClientService(store=client_store, wedding_store=wedding_store)
    wedding_service = WeddingService(client_service=client_service, wedding_store=wedding_store)

    wedding = wedding_service.get_wedding_by_session_id(session_id)
    if wedding is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    response = WeddingResponse(session_id=session_id, wedding=wedding)
    return response
