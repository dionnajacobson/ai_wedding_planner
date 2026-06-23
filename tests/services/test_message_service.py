from typing import Any
from unittest.mock import Mock

from services.message_service import MessageService
from services.types import MessageRole
from tests.services.mock_data import SESSION_ID, mock_message


class TestMessageService:
    """Table-driven tests for MessageService."""

    def test_create_message(self) -> None:
        """Run create-message scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "creates_user_message",
                "message_content": "What venue should we book?",
                "message_role": MessageRole.USER,
            },
            {
                "name": "creates_assistant_message",
                "message_content": "Start with your guest list.",
                "message_role": MessageRole.ASSISTANT,
            },
        ]

        for case in test_cases:
            # ARRANGE
            message_store = Mock()
            message_store.create_message.return_value = mock_message(
                content=case["message_content"],
                role=case["message_role"],
            )
            service = MessageService(store=message_store)

            # ACT
            result = service.create_message(
                SESSION_ID,
                message_content=case["message_content"],
                message_role=case["message_role"],
            )

            # ASSERT
            assert result.content == case["message_content"]
            message_store.create_message.assert_called_once()

    def test_get_messages(self) -> None:
        """Run get-messages scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_messages_from_store",
                "store_return": [
                    mock_message(
                        content="What venue should we book?",
                        role=MessageRole.USER,
                    ),
                    mock_message(
                        content="Start with your guest list.",
                        role=MessageRole.ASSISTANT,
                    ),
                ],
                "expected_content": "What venue should we book?",
            },
            {
                "name": "returns_empty_list",
                "store_return": [],
                "expected_content": None,
            },
        ]

        for case in test_cases:
            # ARRANGE
            message_store = Mock()
            message_store.get_messages.return_value = case["store_return"]
            service = MessageService(store=message_store)

            # ACT
            result = service.get_messages(SESSION_ID)

            # ASSERT
            if case["expected_content"] is not None:
                assert result[0].content == case["expected_content"]
            else:
                assert result == []
            message_store.get_messages.assert_called_once_with(session_id=SESSION_ID)
            message_store.reset_mock()
