from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from .types import LLMPromptInput

JINJA_PROMPTS_DIR = Path(__file__).parent / "templates"


class Prompt(ABC):
    """Render prompts for an LLM."""

    @abstractmethod
    def render(self, **context) -> LLMPromptInput:
        """Render a stored template into a prompt string."""
        pass


class JinjaPrompt(Prompt):
    """Render stored Jinja template files into LLM prompt strings."""

    template_name: str

    def __init__(self, system_context: dict | None = None, user_context: dict | None = None):
        """Initialize the Jinja prompt."""
        # Overridden by subclasses to set the system and user context.
        self.system_context = system_context or {}
        self.user_context = user_context or {}

    def render(self) -> LLMPromptInput:
        """Render system and user blocks into a single prompt string."""
        # Each template defines {% block system %} and {% block user %} in base.jinja.
        # Child templates (e.g. wedding_prompt.jinja) override those blocks via {% extends %}.
        template = self._load_template()
        system = self._render_block("system", self.system_context, template)
        user = self._render_block("user", self.user_context, template)
        prompt = LLMPromptInput(system=system, user=user)
        return prompt

    def _load_template(self) -> Template:
        """Load the template from the prompts/templates/ directory."""
        path = JINJA_PROMPTS_DIR / self.template_name
        env = Environment(
            loader=FileSystemLoader(path.parent),
            autoescape=False,  # Prompt text is not HTML; don't escape {{ variables }}.
        )
        template = env.get_template(path.name)
        return template

    def _render_block(self, block_name: str, context: dict, template: Template) -> str:
        """Render one {% block %} from the template (e.g. 'system' or 'user')."""
        # Build a Jinja context dict from the keyword args passed to render().
        new_context = template.new_context(context)
        # blocks[name] returns a generator of text chunks, not a plain string.
        block = template.blocks[block_name](new_context)
        block_text = "".join(block).strip()
        return block_text
