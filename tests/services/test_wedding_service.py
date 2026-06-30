from typing import Any
from unittest.mock import Mock

import pytest

from services.client_service import ClientService
from services.wedding_service import WeddingService
from tests.services.mock_data import CLIENT_ID, SESSION_ID, mock_client, mock_wedding


class TestWeddingService:
    """Table-driven tests for WeddingService."""

    def test_create_session(self) -> None:
        """Run create-session scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "creates_session_when_wedding_exists",
                "creates_session": True,
                "expected_session_id": SESSION_ID,
                "wedding": mock_wedding(),
            },
            {
                "name": "raises_when_wedding_missing",
                "creates_session": False,
                "wedding": None,
            },
        ]

        for case in test_cases:
            # ARRANGE
            client_service = Mock(spec=ClientService)
            wedding_store = Mock()
            wedding_store.get_wedding_by_client_id.return_value = case["wedding"]
            wedding_store.create_session.return_value = SESSION_ID
            service = WeddingService(
                client_service=client_service,
                wedding_store=wedding_store,
            )

            # ACT
            if case["creates_session"]:
                result = service.create_session(client_id=CLIENT_ID)

                # ASSERT
                assert result == case["expected_session_id"]
                wedding_store.get_wedding_by_client_id.assert_called_once()
                wedding_store.create_session.assert_called_once()
            else:
                with pytest.raises(ValueError, match="Wedding not found"):
                    service.create_session(client_id=CLIENT_ID)

                # ASSERT
                wedding_store.get_wedding_by_client_id.assert_called_once()
                wedding_store.create_session.assert_not_called()

            wedding_store.reset_mock()

    def test_get_wedding_by_session_id(self) -> None:
        """Run get-wedding-by-session scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_wedding_when_session_exists",
                "expected_wedding": mock_wedding(),
                "session_id": SESSION_ID,
            },
            {
                "name": "returns_none_when_session_missing",
                "expected_wedding": None,
                "session_id": SESSION_ID,
            },
        ]

        for case in test_cases:
            # ARRANGE
            client_service = Mock(spec=ClientService)
            wedding_store = Mock()
            wedding_store.get_wedding_by_session_id.return_value = case["expected_wedding"]
            service = WeddingService(
                client_service=client_service,
                wedding_store=wedding_store,
            )

            # ACT
            result = service.get_wedding_by_session_id(case["session_id"])

            # ASSERT
            assert result == case["expected_wedding"]
            wedding_store.get_wedding_by_session_id.assert_called_once_with(case["session_id"])
            wedding_store.reset_mock()

    def test_onboard_client(self) -> None:
        """Run onboard-client scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "delegates_to_client_service",
                "email": "alex@example.com",
                "first_name": "Alex",
                "last_name": "Smith",
                "returned_client": mock_client(email="alex@example.com"),
            },
            {
                "name": "delegates_for_second_couple",
                "email": "sam@example.com",
                "first_name": "Sam",
                "last_name": "Taylor",
                "returned_client": mock_client(
                    email="sam@example.com",
                    first_name="Sam",
                    last_name="Taylor",
                ),
            },
        ]

        for case in test_cases:
            # ARRANGE
            client_service = Mock(spec=ClientService)
            wedding_store = Mock()
            client_service.get_or_create_client.return_value = case["returned_client"]
            service = WeddingService(
                client_service=client_service,
                wedding_store=wedding_store,
            )

            # ACT
            result = service.onboard_client(
                email=case["email"],
                first_name=case["first_name"],
                last_name=case["last_name"],
            )

            # ASSERT
            assert result.email == case["email"]
            client_service.get_or_create_client.assert_called_once()
            client_service.reset_mock()
