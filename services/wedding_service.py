import uuid

from services.client_service import ClientService
from services.stores.wedding_store import WeddingStore
from services.types import Client


class WeddingService:
    """Manage weddings and chat sessions."""

    def __init__(
        self,
        client_service: ClientService,
        wedding_store: WeddingStore,
    ):
        """Initialize the wedding service."""
        self._client_service = client_service
        self._wedding_store = wedding_store

    @staticmethod
    def default() -> "WeddingService":
        """Get the default wedding service."""
        client_service = ClientService.default()
        wedding_store = WeddingStore.default()
        wedding_service = WeddingService(
            client_service=client_service,
            wedding_store=wedding_store,
        )
        return wedding_service

    def create_session(
        self,
        client_id: uuid.UUID,
    ) -> uuid.UUID:
        """Start a chat session for a client and wedding."""
        wedding = self._wedding_store.get_wedding_by_client_id(client_id)
        if wedding is None:
            raise ValueError(f"Wedding not found: {client_id}")
        session_id = self._wedding_store.create_session(
            client_id=client_id,
            wedding_id=wedding.id,
        )
        return session_id

    def onboard_client(
        self,
        email: str,
        first_name: str,
        last_name: str,
    ) -> Client:
        """Create a client and linked wedding."""
        client = self._client_service.get_or_create_client(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return client
