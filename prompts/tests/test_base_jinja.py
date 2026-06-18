from prompts.prompt import JinjaPrompt
from tests.base import BaseDataAssertionTest

class BaseJinjaPrompt(JinjaPrompt):
    """Base Jinja prompt."""
    template_name = "base.jinja"

class TestBaseJinja(BaseDataAssertionTest):
    """Test the base Jinja prompt."""

    overwrite_test_data = False

    def test_base_jinja_e2e(self):
        """Test the base Jinja prompt."""
        prompt = BaseJinjaPrompt()
        rendered = prompt.render()

        self.assert_test_data(rendered, "base_jinja_prompt")
