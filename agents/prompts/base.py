from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

from jinja2 import Environment, FileSystemLoader, Template

from .types import LLMPromptInput

JINJA_PROMPTS_DIR = Path(__file__).parent / "templates"

RuntimeFormatter = Callable[[Any], str]


class Prompt(ABC):
    """Render prompts for an LLM."""

    @abstractmethod
    def render(self, **context) -> LLMPromptInput:
        """Render a stored template into a prompt string."""
        pass


class JinjaPrompt(Prompt):
    """Render stored Jinja template files into LLM prompt strings."""

    template_name: str
    runtime_fields: ClassVar[dict[str, RuntimeFormatter]] = {}

    def __init__(self, system_context: dict | None = None, user_context: dict | None = None):
        """Initialize the Jinja prompt."""
        self.system_context = system_context or {}
        self.user_context = user_context or {}
        self.runtime_context: dict[str, str] = {}

    def update_context(self, **context: Any) -> None:
        """Merge runtime values into the next render.

        Keys listed in ``runtime_fields`` are passed through the registered formatter
        before being stored. All other keys are coerced to strings.
        """
        for key, value in context.items():
            formatter = self.runtime_fields.get(key)
            if formatter is not None:
                self.runtime_context[key] = formatter(value)
                continue

            if isinstance(value, str):
                self.runtime_context[key] = value
            else:
                self.runtime_context[key] = str(value)

    def render(self) -> LLMPromptInput:
        """Render system and user blocks into a single prompt string."""
        template = self._load_template()
        system = self._render_block("system", self.system_context, template)
        user = self._render_block("user", self._user_render_context(), template)
        prompt = LLMPromptInput(system=system, user=user)
        return prompt

    def _user_render_context(self) -> dict[str, str]:
        """Return static user context merged with per-turn runtime values."""
        render_context = {**self.user_context, **self.runtime_context}
        return render_context

    def _load_template(self) -> Template:
        """Load the template from the prompts/templates/ directory."""
        path = JINJA_PROMPTS_DIR / self.template_name
        env = Environment(
            loader=FileSystemLoader(path.parent),
            autoescape=False,
        )
        template = env.get_template(path.name)
        return template

    def _render_block(self, block_name: str, context: dict, template: Template) -> str:
        """Render one {% block %} from the template (e.g. 'system' or 'user')."""
        new_context = template.new_context(context)
        block = template.blocks[block_name](new_context)
        block_text = "".join(block).strip()
        return block_text
