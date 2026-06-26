import uuid

from sqlalchemy.orm import Session, selectinload

from db import models as db
from db.database import SessionLocal
from services.stores.client_store import ClientStore
from services.types import Wedding


class WeddingStore:
    """Persist and load wedding records."""

    def __init__(self, db_session: Session, client_store: ClientStore):
        """Initialize the wedding store."""
        self._db = db_session
        self._client_store = client_store

    @staticmethod
    def default() -> "WeddingStore":
        """Get the default wedding store."""
        client_store = ClientStore.default()
        wedding_store = WeddingStore(db_session=SessionLocal(), client_store=client_store)
        return wedding_store

    def create_wedding(
        self,
        client_id: uuid.UUID,
    ) -> Wedding:
        """Insert a wedding and return the persisted record."""
        record = db.Wedding(client_id=client_id)
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        wedding = self._to_wedding(record)
        return wedding

    def create_session(
        self,
        client_id: uuid.UUID,
        wedding_id: uuid.UUID,
    ) -> uuid.UUID:
        """Insert a session and return its id."""
        record = db.WeddingSession(
            client_id=client_id,
            wedding_id=wedding_id,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record.id

    def get_wedding_by_client_id(self, client_id: uuid.UUID) -> Wedding | None:
        """Load a wedding by client id, including linked clients."""
        record = (
            self._db.query(db.Wedding)
            .options(selectinload(db.Wedding.sessions))
            .filter(db.Wedding.client_id == client_id)
            .one_or_none()
        )
        if record is None:
            return None
        wedding = self._to_wedding(record)
        return wedding

    def _to_wedding(self, record: db.Wedding) -> Wedding:
        """Map a wedding row to a Pydantic model."""
        client = self._client_store.get_client(client_id=record.client_id)
        session_ids = [session.id for session in record.sessions]
        wedding = Wedding(
            budget=record.budget,
            client=client,
            id=record.id,
            location=record.location,
            session_ids=session_ids,
            wedding_date=record.wedding_date,
        )
        return wedding
