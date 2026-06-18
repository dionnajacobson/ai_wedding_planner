from tests.base import PromptDataAssertionTest
from agents.prompts.prompts import BaseJinjaPrompt, WeddingPromptJinja

class TestBaseJinja(PromptDataAssertionTest):
    """Test the base Jinja prompt."""

    overwrite_test_data = False

    def test_base_jinja_e2e(self):
        """Test the base Jinja prompt."""
        prompt = BaseJinjaPrompt()
        rendered = prompt.render()

        self.assert_test_data(rendered, "base_prompt")
        

class TestWeddingPromptJinja(PromptDataAssertionTest):
    """Test the wedding prompt Jinja prompt."""

    overwrite_test_data = False

    def test_wedding_prompt_jinja_e2e(self):
        """Test the wedding prompt Jinja prompt."""
        prompt = WeddingPromptJinja()
        rendered = prompt.render()

        self.assert_test_data(rendered, "wedding_prompt")