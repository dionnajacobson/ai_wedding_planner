"""Result types for the agent runtime."""

from __future__ import annotations

from dataclasses import dataclass

from agents.tools.types import ToolResult


@dataclass
class AgentRunResult:
    """Output from one agent run."""

    content: str
    tool_rounds: int = 0
    tool_results: list[ToolResult] | None = None
