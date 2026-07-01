import uuid

from sqlalchemy.orm import Session, selectinload

from db import models as db
from db.database import SessionLocal
from services.stores.client_store import ClientStore
from services.types import BudgetItem, VenueCandidate, Wedding, WeddingBudget, WeddingVendor


class WeddingStore:
    """Persist and load wedding records."""

    def __init__(self, db_session: Session, client_store: ClientStore):
        """Initialize the wedding store."""
        self._client_store = client_store
        self._db = db_session

    @staticmethod
    def default() -> "WeddingStore":
        """Get the default wedding store."""
        client_store = ClientStore.default()
        wedding_store = WeddingStore(client_store=client_store, db_session=SessionLocal())
        return wedding_store

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

    def create_vendor(
        self,
        wedding_id: uuid.UUID,
        candidate: VenueCandidate,
    ) -> WeddingVendor:
        """Insert a vendor row from a candidate with status 'to_contact'."""
        record = db.WeddingVendor(
            category=candidate.category,
            email=candidate.email,
            estimated_cost=candidate.estimated_cost,
            name=candidate.name,
            notes=candidate.notes,
            phone=candidate.phone,
            photos=candidate.photos,
            status=db.VendorStatus.TO_CONTACT,
            website=candidate.website,
            wedding_id=wedding_id,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        vendor = self._to_vendor(record)
        return vendor

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

    def get_wedding_by_client_id(self, client_id: uuid.UUID) -> Wedding | None:
        """Load a wedding by client id, including linked clients."""
        record = self._query_wedding().filter(db.Wedding.client_id == client_id).one_or_none()
        if record is None:
            return None
        wedding = self._to_wedding(record)
        return wedding

    def get_wedding_by_session_id(self, session_id: uuid.UUID) -> Wedding | None:
        """Load the wedding linked to a chat session."""
        session = (
            self._db.query(db.WeddingSession)
            .filter(db.WeddingSession.id == session_id)
            .one_or_none()
        )
        if session is None:
            return None
        record = self._query_wedding().filter(db.Wedding.id == session.wedding_id).one_or_none()
        if record is None:
            return None
        wedding = self._to_wedding(record)
        return wedding

    def _query_wedding(self):
        """Return a wedding query with related profile data eager-loaded."""
        query = self._db.query(db.Wedding).options(
            selectinload(db.Wedding.budget_items),
            selectinload(db.Wedding.sessions),
            selectinload(db.Wedding.vendors),
        )
        return query

    def _to_budget_item(self, record: db.BudgetItem) -> BudgetItem:
        """Map a budget item row to a Pydantic model."""
        item = BudgetItem(
            actual_amount=record.actual_amount,
            category=record.category,
            estimated_amount=record.estimated_amount,
            id=record.id,
            name=record.name,
            notes=record.notes,
        )
        return item

    def _to_vendor(self, record: db.WeddingVendor) -> WeddingVendor:
        """Map a vendor row to a Pydantic model."""
        vendor = WeddingVendor(
            category=record.category,
            email=record.email,
            estimated_cost=record.estimated_cost,
            id=record.id,
            name=record.name,
            notes=record.notes,
            phone=record.phone,
            photos=list(record.photos or []),
            status=record.status,
            website=record.website,
        )
        return vendor

    def _to_wedding(self, record: db.Wedding) -> Wedding:
        """Map a wedding row to a Pydantic model."""
        client = self._client_store.get_client(client_id=record.client_id)
        session_ids = [session.id for session in record.sessions]
        budget_items = [self._to_budget_item(item) for item in record.budget_items]
        vendors = [self._to_vendor(vendor) for vendor in record.vendors]
        budget = WeddingBudget(budget_cap=record.budget_cap, items=budget_items)
        wedding = Wedding(
            budget=budget,
            budget_cap=record.budget_cap,
            client=client,
            guest_count=record.guest_count,
            id=record.id,
            location=record.location,
            notes=record.notes,
            session_ids=session_ids,
            style=list(record.style or []),
            vendors=vendors,
            wedding_date=record.wedding_date,
        )
        return wedding
