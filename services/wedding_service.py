import uuid

from services.stores.message_store import MessageStore
from services.stores.wedding_store import WeddingStore
from services.types import (
    Message,
    Wedding,
    Client,
)
from services.client_service import ClientService
from services.types import MessageRole


class WeddingService:
    """Manage weddings, chat sessions, and messages."""

    def __init__(
        self,
        message_store: MessageStore,
        client_store: ClientService,
        wedding_store: WeddingStore,
    ):
        """Initialize the wedding service."""
        self._message_store = message_store
        self._client_store = client_store
        self._wedding_store = wedding_store

    @staticmethod
    def default() -> "WeddingService":
        """Get the default wedding service."""
        message_store = MessageStore.default()
        client_store = ClientService.default()
        wedding_store = WeddingStore.default()
        wedding_service = WeddingService(message_store=message_store, session_store=session_store, client_store=client_store, wedding_store=wedding_store)
        return wedding_service

    def record_message(
        self,
        session_id: uuid.UUID,
        message_role: MessageRole,
        message_content: str,
    ) -> Message:
        """Append a user message and assistant reply to a session."""
        self._message_store.create_message(
            session_id=session_id,
            message_role=message_role,
            message_content=message_content,
        )

    def create_session(
        self,
        client_id: uuid.UUID,
    ) -> uuid.UUID:
        """Start a chat session for a client and wedding."""
        wedding = self._wedding_store.get_wedding_by_client_id(client_id)
        if wedding is None:
            raise ValueError(f"Wedding not found: {client_id}")
        session_id = self._wedding_store.create_session(client_id=client_id, wedding_id=wedding.id)
        return session_id

    def onboard_client(
        self,
        email: str,
        first_name: str,
        last_name: str,
    ) -> Client:
        """Create a wedding and linked client users from couple details."""
        client = self._client_store.get_or_create_client(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return client
