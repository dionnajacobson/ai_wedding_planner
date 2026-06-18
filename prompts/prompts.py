from prompts.base import JinjaPrompt

class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""
    
    template_name = "base.jinja"


class WeddingPromptJinja(JinjaPrompt):
    """Wedding prompt Jinja prompt."""

    template_name = "wedding_prompt.jinja"

    def __init__(self,  budget: str = "Unknown", couple_names: str = "Unknown", wedding_date: str = "Unknown"):
        """Initialize the wedding prompt Jinja prompt."""
        system_context = {
            "couple_names": couple_names,
            "wedding_date": wedding_date,
            "budget": budget,
        }
        super().__init__(system_context=system_context)