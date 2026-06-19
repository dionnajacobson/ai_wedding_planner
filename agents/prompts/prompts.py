from xml.sax.saxutils import escape

from agents.prompts.base import JinjaPrompt
from services.types import Message


def format_history_as_xml(messages: list[Message]) -> str:
    """F
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


class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""

    template_name = "base.jinja"


class WeddingPromptJinja(JinjaPrompt):
    """Wedding prompt Jinja prompt."""

    template_name = "wedding_prompt.jinja"

    def __init__(
        self,
        query: str,
        messages: list[Message] | None = None,
    ):
        """Initialize the wedding prompt Jinja prompt."""
        history = format_history_as_xml(messages or [])
        system_context = {
            "budget": "Unknown",
            "couple_names": "Unknown",
            "guest_count": "Unknown",
            "wedding_date": "Unknown",
        }
        user_context = {
            "history": history,
            "query": query,
        }
        super().__init__(system_context=system_context, user_context=user_context)
