import uuid

from services.stores.client_store import ClientStore
from services.stores.wedding_store import WeddingStore
from services.types import Client


class ClientService:
    """Manage client records."""

    def __init__(self, store: ClientStore, wedding_store: WeddingStore):
        """Initialize the ClientService."""
        self._client_store = store
        self._wedding_store = wedding_store

    @staticmethod
    def default() -> "ClientService":
        """Get the default client service."""
        client_store = ClientStore.default()
        wedding_store = WeddingStore.default()
        client_service = ClientService(store=client_store, wedding_store=wedding_store)
        return client_service

    def get_or_create_client(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
    ) -> Client:
        """Create a client linked to an optional wedding."""
        client = self._client_store.get_client(email=email)
        if client is None:
            client = self._client_store.create_client(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            # Attach the client to a new wedding
            wedding = self._wedding_store.create_wedding(client_id=client.id)
            client.wedding_id = wedding.id

        return client

    def get_client(self, client_id: uuid.UUID) -> Client | None:
        """Return a client by id."""
        client = self._client_store.get_client(client_id=client_id)
        return client
