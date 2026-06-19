from typing import Any
from unittest.mock import Mock

from services.client_service import ClientService
from tests.services.mock_data import mock_client, mock_wedding


class TestClientService:
    """Table-driven tests for ClientService."""

    def test_get_or_create_client(self) -> None:
        """Run get-or-create scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "returns_existing_client",
                "email": "alex@example.com",
                "existing_client": mock_client(email="alex@example.com"),
                "creates_client": False,
            },
            {
                "name": "creates_client_and_wedding",
                "email": "jordan@example.com",
                "first_name": "Jordan",
                "last_name": "Lee",
                "existing_client": None,
                "created_client": mock_client(
                    email="jordan@example.com",
                    first_name="Jordan",
                    last_name="Lee",
                    wedding_id=None,
                ),
                "creates_client": True,
            },
        ]

        for case in test_cases:
            # ARRANGE
            client_store = Mock()
            wedding_store = Mock()
            client_store.get_client.return_value = case["existing_client"]

            if case["creates_client"]:
                client_store.create_client.return_value = case["created_client"]
                wedding_store.create_wedding.return_value = mock_wedding(
                    client=case["created_client"]
                )

            service = ClientService(store=client_store, wedding_store=wedding_store)

            # ACT
            result = service.get_or_create_client(
                email=case["email"],
                first_name=case.get("first_name", "Alex"),
                last_name=case.get("last_name", "Smith"),
            )

            # ASSERT
            assert result.email == case["email"]
            client_store.get_client.assert_called_once_with(email=case["email"])

            if case["creates_client"]:
                client_store.create_client.assert_called_once()
                wedding_store.create_wedding.assert_called_once()
            else:
                client_store.create_client.assert_not_called()
                wedding_store.create_wedding.assert_not_called()

            client_store.reset_mock()
            wedding_store.reset_mock()
