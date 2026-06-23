import uuid

from sqlalchemy.orm import Session

from db import models as db
from db.database import SessionLocal
from services.types import Client


class ClientStore:
    """Persist and load client records."""

    def __init__(self, db_session: Session):
        """Initialize the client store."""
        self._db = db_session

    @staticmethod
    def default() -> "ClientStore":
        """Get the default client store."""
        client_store = ClientStore(db_session=SessionLocal())
        return client_store

    def create_client(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
    ) -> Client:
        """Insert a client and return the persisted record."""
        record = db.Client(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        client = self._to_client(record)
        return client

    def get_client(
        self, *, client_id: uuid.UUID | None = None, email: str | None = None
    ) -> Client | None:
        """Load a client by id or email ."""
        if client_id is not None:
            record = self._db.query(db.Client).filter(db.Client.id == client_id).one_or_none()
        else:
            record = self._db.query(db.Client).filter(db.Client.email == email).one_or_none()

        if record is None:
            return None

        client = self._to_client(record)
        return client

    def _to_client(self, record: db.Client) -> Client:
        """Map a client row to a Pydantic model."""
        wedding_id = record.wedding.id if record.wedding else None
        client = Client(
            email=record.email,
            first_name=record.first_name,
            id=record.id,
            last_name=record.last_name,
            wedding_id=wedding_id,
        )
        return client
