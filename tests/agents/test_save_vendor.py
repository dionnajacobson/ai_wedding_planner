"""Unit tests for the save_vendor tool."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import Mock

import pytest

from agents.agent.types import ToolEntry
from agents.tools.tools.save_vendor import SaveVendorDefinition, SaveVendorExecutor
from agents.tools.types import ToolCall
from services.wedding_service import WeddingService
from tests.services.mock_data import SESSION_ID, mock_vendor, mock_wedding


class TestSaveVendorExecutor:
    """Table-driven tests for SaveVendorExecutor."""

    def test_execute_saves_candidate_for_the_definitions_session(self) -> None:
        """Run save-vendor execution scenarios from the test table."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "saves_candidate_with_to_contact_status",
                "arguments": {"category": "photography", "name": "Lens & Light Studio"},
                "returned_vendor": mock_vendor(),
                "expected_content": "Saved vendor 'Lens & Light Studio' with status 'researching'.",
            },
        ]

        for case in test_cases:
            # ARRANGE
            wedding = mock_wedding()
            wedding_service = Mock(spec=WeddingService)
            wedding_service.get_wedding_by_session_id.return_value = wedding
            wedding_service.add_vendor.return_value = case["returned_vendor"]
            executor = SaveVendorExecutor(wedding_service=wedding_service)
            tool_call = ToolCall(id="call_1", name="save_vendor", arguments=case["arguments"])
            entry = ToolEntry(definition=SaveVendorDefinition(session_id=SESSION_ID))

            # ACT
            result = asyncio.run(executor.execute(tool_call, tool_entry=entry, runner=None))

            # ASSERT
            assert result.tool_call_id == "call_1"
            assert result.content == case["expected_content"]
            wedding_service.get_wedding_by_session_id.assert_called_once_with(SESSION_ID)
            wedding_service.add_vendor.assert_called_once()
            call_kwargs = wedding_service.add_vendor.call_args.kwargs
            assert call_kwargs["wedding_id"] == wedding.id
            assert call_kwargs["candidate"].name == case["arguments"]["name"]

    def test_execute_raises_when_wedding_missing(self) -> None:
        """Run scenarios where no wedding is linked to the definition's session."""
        test_cases: list[dict[str, Any]] = [
            {
                "name": "raises_when_session_has_no_wedding",
                "arguments": {"category": "photography", "name": "Lens & Light Studio"},
            },
        ]

        for case in test_cases:
            # ARRANGE
            wedding_service = Mock(spec=WeddingService)
            wedding_service.get_wedding_by_session_id.return_value = None
            executor = SaveVendorExecutor(wedding_service=wedding_service)
            tool_call = ToolCall(id="call_1", name="save_vendor", arguments=case["arguments"])
            entry = ToolEntry(definition=SaveVendorDefinition(session_id=SESSION_ID))

            # ACT / ASSERT
            with pytest.raises(ValueError, match="Wedding not found"):
                asyncio.run(executor.execute(tool_call, tool_entry=entry, runner=None))

    def test_execute_raises_without_session_id(self) -> None:
        """Run scenarios where the definition has no bound session id."""
        test_cases: list[dict[str, Any]] = [
            {"name": "raises_when_definition_lacks_session_id"},
        ]

        for _case in test_cases:
            # ARRANGE
            executor = SaveVendorExecutor(wedding_service=Mock(spec=WeddingService))
            tool_call = ToolCall(
                id="call_1",
                name="save_vendor",
                arguments={"category": "photography", "name": "Lens & Light Studio"},
            )
            entry = ToolEntry(definition=SaveVendorDefinition())

            # ACT / ASSERT
            with pytest.raises(ValueError, match="requires a SaveVendorDefinition"):
                asyncio.run(executor.execute(tool_call, tool_entry=entry, runner=None))

    def test_session_id_survives_definition_reconstruction(self) -> None:
        """Run scenarios confirming session_id round-trips through the definition."""
        test_cases: list[dict[str, Any]] = [
            {"name": "keeps_the_provided_session_id", "session_id": uuid.uuid4()},
        ]

        for case in test_cases:
            # ACT
            definition = SaveVendorDefinition(session_id=case["session_id"])

            # ASSERT
            assert definition.session_id == case["session_id"]
