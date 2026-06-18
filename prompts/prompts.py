from prompts.base import JinjaPrompt

class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""
    
    template_name = "base.jinja"


class WeddingPromptJinja(JinjaPrompt):
    """Wedding prompt Jinja prompt."""

    template_name = "wedding_prompt.jinja"

    def _get_system_context(self) -> dict:
        """Get the system context for the wedding prompt Jinja prompt."""
        context = {
            "couple_names": "Unknown",
            "wedding_date": "Unknown",
            "budget": "Unknown",
        }
        return context