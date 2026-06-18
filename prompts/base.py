from abc import ABC, abstractmethod

class Prompt(ABC):
    """Render prompts for an LLM."""

    @abstractmethod
    def render(self, **context) -> str:
        """Render a stored template into a prompt string."""
        pass
