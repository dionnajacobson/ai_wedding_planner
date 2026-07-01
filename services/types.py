from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field, computed_field

from db.models import BudgetCategory, MessageRole, VendorCategory, VendorStatus


class BudgetItem(BaseModel):
    """A planned or actual expense line on the wedding budget."""

    actual_amount: float | None = None
    category: BudgetCategory
    estimated_amount: float
    id: uuid.UUID
    name: str
    notes: str | None = None


class Client(BaseModel):
    """User model."""

    email: str
    first_name: str
    id: uuid.UUID
    last_name: str
    wedding_id: uuid.UUID | None = None


class Message(BaseModel):
    """Message model."""

    content: str
    id: uuid.UUID
    role: MessageRole


class VenueCandidate(BaseModel):
    """A vendor candidate to save — bring-your-own or found via vendor search."""

    category: VendorCategory
    contact_info: str | None = None
    estimated_cost: float | None = None
    name: str
    notes: str | None = None


class WeddingBudget(BaseModel):
    """Budget totals and line items for display in chat."""

    budget_cap: float | None = None
    items: list[BudgetItem]

    @computed_field
    @property
    def allocated(self) -> float:
        """Sum of estimated amounts across budget line items."""
        allocated = sum(item.estimated_amount for item in self.items)
        return allocated

    @computed_field
    @property
    def remaining(self) -> float | None:
        """Budget headroom when a budget cap is set."""
        if self.budget_cap is None:
            return None
        remaining = self.budget_cap - self.allocated
        return remaining


class WeddingVendor(BaseModel):
    """A vendor the couple is researching or has booked."""

    category: VendorCategory
    contact_info: str | None = None
    estimated_cost: float | None = None
    id: uuid.UUID
    name: str
    notes: str | None = None
    status: VendorStatus


class Wedding(BaseModel):
    """Wedding profile returned to the chat UI and agent layer."""

    budget: WeddingBudget
    budget_cap: float | None = None
    client: Client
    guest_count: int | None = None
    id: uuid.UUID
    location: str | None = None
    notes: str | None = None
    session_ids: list[uuid.UUID]
    style: list[str] = Field(default_factory=list)
    vendors: list[WeddingVendor]
    wedding_date: date | None = None
