from pydantic import BaseModel


class LLMPromptInput(BaseModel):
    """Input to an LLM."""

    system: str
    user: str
