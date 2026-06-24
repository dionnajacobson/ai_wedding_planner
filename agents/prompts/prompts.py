from xml.sax.saxutils import escape

from agents.prompts.base import JinjaPrompt
from agents.tools.types import ToolResult
from services.types import Message


def format_history_as_xml(messages: list[Message]) -> str:
    """
    Format session messages as XML for the prompt.
    TODO: Make History Service
    """
    parts = ["<history>"]
    for message in messages:
        content = escape(message.content)
        role = message.role.value
        parts.append(f'  <message role="{role}">{content}</message>')
    parts.append("</history>")
    history = "\n".join(parts)
    return history


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


class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""

    template_name = "base.jinja"


class WeddingPromptJinja(JinjaPrompt):
    """Wedding prompt Jinja prompt."""

    template_name = "wedding_prompt.jinja"
    runtime_fields = {"tool_results": format_tool_results_as_xml}

    def __init__(
        self,
        query: str,
        messages: list[Message] | None = None,
        tool_results: list[ToolResult] | None = None,
    ):
        """Initialize the wedding prompt Jinja prompt."""
        history = format_history_as_xml(messages or [])
        user_context = {
            "history": history,
            "query": query,
        }
        super().__init__(user_context=user_context)
        if tool_results:
            self.update_context(tool_results=tool_results)
