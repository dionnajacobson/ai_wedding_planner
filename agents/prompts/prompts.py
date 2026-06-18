from agents.prompts.base import JinjaPrompt

class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""
    
    template_name = "base.jinja"


class WeddingPromptJinja(JinjaPrompt):
    """Wedding prompt Jinja prompt."""

    template_name = "wedding_prompt.jinja"

    def __init__(
        self,
        query: str,
        budget: str = "Unknown",
        couple_names: str = "Unknown",
        wedding_date: str = "Unknown",
        guest_count: str = "Unknown",
    ):
        """Initialize the wedding prompt Jinja prompt."""
        system_context = {
            "couple_names": couple_names,
            "wedding_date": wedding_date,
            "budget": budget,
            "guest_count": guest_count,
        }
        user_context = {
            "query": query,
        }
        super().__init__(system_context=system_context, user_context=user_context)