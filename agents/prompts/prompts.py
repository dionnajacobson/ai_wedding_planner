from xml.sax.saxutils import escape

from agents.prompts.base import JinjaPrompt
from agents.tools.types import ToolDefinition, ToolResult
from services.types import Message


def format_history_as_xml(history: list[Message]) -> str:
    """
    Format session history as XML for the prompt.
    TODO: Make History Service
    """
    parts = ["<history>"]
    for message in history:
        content = escape(message.content)
        role = message.role.value
        parts.append(f'  <message role="{role}">{content}</message>')
    parts.append("</history>")
    formatted = "\n".join(parts)
    return formatted


def format_tool_results_as_xml(tool_results: list[ToolResult]) -> str:
    """Format tool results from the current turn as XML for the prompt."""
    if not tool_results:
        text = ""
        return text

    parts = ["<tool_results>"]
    for result in tool_results:
        content = escape(result.content)
        tool_call_id = escape(result.tool_call_id, {'"': "&quot;"})
        parts.append(f'  <result tool_call_id="{tool_call_id}">{content}</result>')
    parts.append("</tool_results>")
    text = "\n".join(parts)
    return text


def format_tool_descriptions(tools: list[ToolDefinition]) -> str:
    """Format available tool definitions as XML for the prompt."""
    if not tools:
        return ""

    parts = ["<tools>"]
    for tool in tools:
        name = escape(tool.name_formatted)
        description = escape(tool.description)
        parts.append(f'  <tool name="{name}">{description}</tool>')
    parts.append("</tools>")
    return "\n".join(parts)


class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""

    template_name = "base.jinja"


class AgentJinjaPrompt(JinjaPrompt):
    """Jinja prompt with shared conversation, history, and tool context."""

    runtime_fields = {
        "tool_results": format_tool_results_as_xml,
        "tool_descriptions": format_tool_descriptions,
    }

    def __init__(
        self,
        *,
        query: str = "",
        task: str = "",
        history: list[Message] | None = None,
        tool_results: list[ToolResult] | None = None,
        tool_descriptions: list[ToolDefinition] | None = None,
        system_context: dict | None = None,
    ):
        """Initialize shared user context for agent prompts."""
        user_context = {
            "history": format_history_as_xml(history or []),
            "query": query,
            "task": task,
        }
        super().__init__(system_context=system_context, user_context=user_context)
        if tool_results:
            self.update_context(tool_results=tool_results)
        if tool_descriptions:
            self.update_context(tool_descriptions=tool_descriptions)


class WeddingPromptJinja(AgentJinjaPrompt):
    """Wedding planner prompt."""

    template_name = "wedding_prompt.jinja"


class VendorSearchPromptJinja(AgentJinjaPrompt):
    """Vendor search sub-agent prompt."""

    template_name = "vendor_search_prompt.jinja"
