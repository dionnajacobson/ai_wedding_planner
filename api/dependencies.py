"""Process-lifetime dependencies shared across API requests."""

from fastapi import Request

from agents.agent import AgentRunner


def get_agent_runner(request: Request) -> AgentRunner:
    """Return the shared agent runner so MCP sessions are reused across requests."""
    return request.app.state.agent_runner
