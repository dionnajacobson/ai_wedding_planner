import uuid

from services.types import Client, Message, MessageRole, Wedding

CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
WEDDING_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
SESSION_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
USER_MESSAGE_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
ASSISTANT_MESSAGE_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


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


def mock_wedding(
    *,
    client: Client | None = None,
    id: uuid.UUID = WEDDING_ID,
    session_ids: list[uuid.UUID] | None = None,
) -> Wedding:
    """Build a wedding for service tests."""
    wedding = Wedding(
        client=client or mock_client(),
        id=id,
        session_ids=session_ids or [SESSION_ID],
    )
    return wedding


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
