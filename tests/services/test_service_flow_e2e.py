from typing import Any
from unittest.mock import Mock

from services.client_service import ClientService
from services.message_service import MessageService
from services.types import MessageRole
from services.wedding_service import WeddingService
from tests.services.mock_data import mock_client, mock_message, mock_wedding


class TestServiceFlowE2E:
    """Table-driven mocked end-to-end flows across services."""

    def test_onboard_session_and_messages(self) -> None:
        """Run cross-service scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "onboard_session_and_message_flow",
                "email": "alex@example.com",
                "first_name": "Alex",
                "last_name": "Smith",
                "user_message_content": "What should we book first?",
                "assistant_message_content": "Start with your venue and date.",
            },
        ]

        for case in test_cases:
            # ARRANGE
            client_store = Mock()
            wedding_store = Mock()
            message_store = Mock()

            created_client = mock_client(
                email=case["email"],
                first_name=case["first_name"],
                last_name=case["last_name"],
                wedding_id=None,
            )
            wedding = mock_wedding(client=created_client)

            client_store.get_client.return_value = None
            client_store.create_client.return_value = created_client
            wedding_store.create_wedding.return_value = wedding
            wedding_store.get_wedding_by_client_id.return_value = wedding
            wedding_store.create_session.return_value = wedding.session_ids[0]
            message_store.create_message.side_effect = [
                mock_message(
                    content=case["user_message_content"],
                    role=MessageRole.USER,
                ),
                mock_message(
                    content=case["assistant_message_content"],
                    role=MessageRole.ASSISTANT,
                ),
            ]

            client_service = ClientService(store=client_store, wedding_store=wedding_store)
            wedding_service = WeddingService(
                client_service=client_service,
                wedding_store=wedding_store,
            )
            message_service = MessageService(store=message_store)

            # ACT
            client = wedding_service.onboard_client(
                email=case["email"],
                first_name=case["first_name"],
                last_name=case["last_name"],
            )
            session_id = wedding_service.create_session(client_id=client.id)
            user_message = message_service.create_message(
                session_id,
                message_content=case["user_message_content"],
                message_role=MessageRole.USER,
            )
            assistant_message = message_service.create_message(
                session_id,
                message_content=case["assistant_message_content"],
                message_role=MessageRole.ASSISTANT,
            )

            # ASSERT
            assert client.email == case["email"]
            assert user_message.content == case["user_message_content"]
            assert assistant_message.content == case["assistant_message_content"]
            client_store.create_client.assert_called_once()
            wedding_store.create_wedding.assert_called_once()
            wedding_store.create_session.assert_called_once()
            assert message_store.create_message.call_count == 2

            client_store.reset_mock()
            wedding_store.reset_mock()
            message_store.reset_mock()
