from typing import Any
from unittest.mock import Mock

from services.message_service import MessageService
from services.tests.mock_data import SESSION_ID, mock_message
from services.types import MessageRole


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
            message_store.reset_mock()
