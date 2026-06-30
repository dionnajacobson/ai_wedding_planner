import uuid
from datetime import date

from db.models import BudgetCategory, MessageRole, VendorCategory, VendorStatus
from services.types import BudgetItem, Client, Message, Wedding, WeddingBudget, WeddingVendor

CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
WEDDING_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
SESSION_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
USER_MESSAGE_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
ASSISTANT_MESSAGE_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
BUDGET_ITEM_ID = uuid.UUID("66666666-6666-6666-6666-666666666666")
VENDOR_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")


def mock_budget_item(
    *,
    category: BudgetCategory = BudgetCategory.VENUE,
    estimated_amount: float = 8000.0,
    id: uuid.UUID = BUDGET_ITEM_ID,
    name: str = "Venue deposit",
) -> BudgetItem:
    """Build a budget line item for service tests."""
    item = BudgetItem(
        category=category,
        estimated_amount=estimated_amount,
        id=id,
        name=name,
    )
    return item


def mock_client(
    *,
    email: str = "alex@example.com",
    first_name: str = "Alex",
    id: uuid.UUID = CLIENT_ID,
    last_name: str = "Smith",
    wedding_id: uuid.UUID | None = WEDDING_ID,
) -> Client:
    """Build a client for service tests."""
    client = Client(
        email=email,
        first_name=first_name,
        id=id,
        last_name=last_name,
        wedding_id=wedding_id,
    )
    return client


def mock_message(
    *,
    content: str = "Hello",
    id: uuid.UUID = USER_MESSAGE_ID,
    role: MessageRole = MessageRole.USER,
) -> Message:
    """Build a message for service tests."""
    message = Message(
        content=content,
        id=id,
        role=role,
    )
    return message


def mock_vendor(
    *,
    category: VendorCategory = VendorCategory.PHOTOGRAPHY,
    id: uuid.UUID = VENDOR_ID,
    name: str = "Lens & Light Studio",
    status: VendorStatus = VendorStatus.RESEARCHING,
) -> WeddingVendor:
    """Build a vendor for service tests."""
    vendor = WeddingVendor(
        category=category,
        id=id,
        name=name,
        status=status,
    )
    return vendor


def mock_wedding(
    *,
    budget_cap: float | None = 35000.0,
    budget_items: list[BudgetItem] | None = None,
    client: Client | None = None,
    guest_count: int | None = 120,
    id: uuid.UUID = WEDDING_ID,
    location: str | None = "Austin, TX",
    session_ids: list[uuid.UUID] | None = None,
    style: list[str] | None = None,
    vendors: list[WeddingVendor] | None = None,
    wedding_date: date | None = date(2026, 9, 12),
) -> Wedding:
    """Build a wedding for service tests."""
    items = budget_items if budget_items is not None else [mock_budget_item()]
    vendor_list = vendors if vendors is not None else [mock_vendor()]
    styles = style if style is not None else ["garden", "formal"]
    budget = WeddingBudget(budget_cap=budget_cap, items=items)
    wedding = Wedding(
        budget=budget,
        budget_cap=budget_cap,
        client=client or mock_client(),
        guest_count=guest_count,
        id=id,
        location=location,
        session_ids=session_ids or [SESSION_ID],
        style=styles,
        vendors=vendor_list,
        wedding_date=wedding_date,
    )
    return wedding
