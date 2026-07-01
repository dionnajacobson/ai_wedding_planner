"""Save a vendor candidate — BYO or from discovery — to a wedding's vendor list."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from agents.tools.protocols import ToolExecutor
from agents.tools.types import ToolCall, ToolDefinition, ToolName, ToolResult
from services.types import VenueCandidate
from services.wedding_service import WeddingService

if TYPE_CHECKING:
    from agents.agent.types import ToolEntry


class SaveVendorDefinition(ToolDefinition):
    """Schema exposed to the LLM for the save_vendor tool.

    Carries `session_id` so the wedding a call belongs to is resolved from
    the request that built this definition, never from the LLM.
    """

    description: str = (
        "Save a vendor candidate — bring-your-own or found via vendor search — "
        "to the wedding's vendor list with status 'to_contact'."
    )
    name: ToolName = ToolName.SAVE_VENDOR
    params_model: type[VenueCandidate] = VenueCandidate
    session_id: uuid.UUID | None = None


class SaveVendorExecutor(ToolExecutor):
    """Persist a vendor candidate for the wedding linked to a session.

    Stateless: the session id comes from the `SaveVendorDefinition` passed in
    per call (built fresh per request), not from constructor state.
    """

    def __init__(self, wedding_service: WeddingService | None = None) -> None:
        """Optionally pin a wedding service for tests; production builds default() per call."""
        self._wedding_service = wedding_service

    async def execute(
        self,
        tool_call: ToolCall,
        tool_entry: ToolEntry,
        runner: Any,
    ) -> ToolResult:
        """Resolve the wedding for the definition's session and save the candidate."""
        definition = tool_entry.definition
        session_id = definition.session_id if isinstance(definition, SaveVendorDefinition) else None
        if session_id is None:
            raise ValueError("save_vendor requires a SaveVendorDefinition with session_id set.")

        candidate = VenueCandidate.model_validate(tool_call.arguments)
        service = self._wedding_service or WeddingService.default()
        wedding = service.get_wedding_by_session_id(session_id)
        if wedding is None:
            raise ValueError(f"Wedding not found for session: {session_id}")

        vendor = service.add_vendor(wedding_id=wedding.id, candidate=candidate)
        content = f"Saved vendor '{vendor.name}' with status '{vendor.status.value}'."
        result = ToolResult(content=content, tool_call_id=tool_call.id)
        return result
