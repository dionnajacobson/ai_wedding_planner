from agents.agent.types import Agent, AgentRunResult, ToolEntry
from agents.tools.tools.agent_tool import AgentToolDefinition, AgentToolExecutor, AgentToolInput

__all__ = [
    "Agent",
    "AgentRunResult",
    "AgentRunner",
    "AgentToolDefinition",
    "AgentToolExecutor",
    "AgentToolInput",
    "ToolEntry",
]


def __getattr__(name: str):
    """Lazy-load AgentRunner to avoid circular imports with ToolOrchestrator."""
    if name == "AgentRunner":
        from agents.agent.agent import AgentRunner

        return AgentRunner
    message = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(message)
