from abc import ABC, abstractmethod
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class Prompt(ABC):
    """Render prompts for an LLM."""

    @abstractmethod
    def render(self, **context) -> str:
        """Render a stored template into a prompt string."""
        pass


class JinjaPrompt(Prompt):
    """Render stored Jinja template files into LLM prompt strings."""

    template_name: str

    def __init__(self):
        path = Path("prompts", "templates", self.template_name)
        # Load templates from prompts/templates/ (subclasses set template_name).
        self.env = Environment(
            loader=FileSystemLoader(path.parent),
            autoescape=False,  # Prompt text is not HTML; don't escape {{ variables }}.
        )
        self.template = self.env.get_template(path.name)

    def _render_block(self, block_name: str, context: dict) -> str:
        """Render one {% block %} from the template (e.g. 'system' or 'user')."""
        # Build a Jinja context dict from the keyword args passed to render().
        new_context = self.template.new_context(context)
        # blocks[name] returns a generator of text chunks, not a plain string.
        block = self.template.blocks[block_name](new_context)
        block_text = "".join(block).strip()
        return block_text

    def render(self) -> str:
        """Render system and user blocks into a single prompt string."""
        # Each template defines {% block system %} and {% block user %} in base.jinja.
        # Child templates (e.g. wedding_prompt.jinja) override those blocks via {% extends %}.
        system_context = self._get_system_context()
        user_context = self._get_user_context()
        system = self._render_block("system", system_context)
        user = self._render_block("user", user_context)
        prompt = f"{system}\n\n{user}"
        return prompt
    
    def _get_system_context(self) -> dict:
        """Get the system context for the Jinja prompt."""
        return {}

    def _get_user_context(self) -> dict:
        """Get the user context for the Jinja prompt."""
        return {}