import uuid

from sqlalchemy.orm import Session

from db import models as db
from db.database import SessionLocal
from services.types import Message, MessageRole


class MessageStore:
    """Persist and load chat messages."""

    def __init__(self, db_session: Session):
        """Initialize the message store."""
        self._db = db_session

    @staticmethod
    def default() -> "MessageStore":
        """Get the default message store."""
        session = SessionLocal()
        message_store = MessageStore(db_session=session)
        return message_store

    def create_message(
        self,
        session_id: uuid.UUID,
        message_role: MessageRole,
        message_content: str = "",
    ) -> Message:
        """Insert a user message and assistant reply for a session."""
        message = db.Message(
            content=message_content,
            role=message_role,
            session_id=session_id,
        )
        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)
        message = self._to_message(message)
        return message

    def get_messages(self, session_id: uuid.UUID) -> list[Message]:
        """Get all messages for a session."""
        records = (
            self._db.query(db.Message)
            .filter(db.Message.session_id == session_id)
            .order_by(db.Message.created_at)
            .all()
        )
        messages = [self._to_message(message) for message in records]
        return messages

    def _to_message(self, record: db.Message) -> Message:
        """Map a message row to a Pydantic model."""
        message = Message(
            content=record.content,
            id=record.id,
            role=MessageRole(record.role.value),
        )
        return message