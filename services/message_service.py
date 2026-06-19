import uuid

from services.stores.message_store import MessageStore
from services.types import Message, MessageRole


class MessageService:
    """Manage chat message records."""

    def __init__(self, store: MessageStore):
        """Initialize the message service."""
        self._store = store

    @staticmethod
    def default() -> "MessageService":
        """Get the default message service."""
        store = MessageStore.default()
        message_service = MessageService(store=store)
        return message_service

    def create_message(
        self,
        session_id: uuid.UUID,
        *,
        message_content: str,
        message_role: MessageRole,
    ) -> Message:
        """Persist a single message for a session."""
        message = self._store.create_message(
            message_content=message_content,
            message_role=message_role,
            session_id=session_id,
        )
        return message

    def get_messages(self, session_id: uuid.UUID) -> list[Message]:
        """Get all messages for a session."""
        messages = self._store.get_messages(session_id=session_id)
        return messages