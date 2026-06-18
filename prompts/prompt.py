from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from prompts.base import Prompt

SYSTEM_MARKER = "<<<SYSTEM>>>"
USER_MARKER = "<<<USER>>>"


class JinjaPrompt(Prompt):
    """Render stored Jinja template files into LLM prompt strings."""

    template_name: str

    def __init__(self):
        path = Path("prompts", "templates", self.template_name)
        self.env = Environment(
            loader=FileSystemLoader(path.parent),
            autoescape=False,
        )
        self.template = self.env.get_template(path.name)

    def render(self, **context) -> str:
        """Render the full template (system + user sections with markers)."""
        rendered = self.template.render(**context)
        _, after_system = rendered.split(SYSTEM_MARKER, 1)
        system, user = after_system.split(USER_MARKER, 1)
        prompt = f"{system.strip()}\n{user.strip()}"
        return prompt

