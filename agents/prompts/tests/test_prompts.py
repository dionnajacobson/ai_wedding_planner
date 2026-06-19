from tests.base import PromptDataAssertionTest
from agents.prompts.prompts import BaseJinjaPrompt, WeddingPromptJinja
from services.tests.mock_data import mock_message
from services.types import MessageRole

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
        mock_messages = [
            mock_message(content="We are getting married in 6 months and need to plan a wedding.", role=MessageRole.USER), 
            mock_message(content="We need to book a venue, caterer, and photographer.", role=MessageRole.ASSISTANT)  
        ]
        prompt = WeddingPromptJinja(query="What should we focus on next?", messages=mock_messages)
        rendered = prompt.render()

        self.assert_test_data(rendered, "wedding_prompt")