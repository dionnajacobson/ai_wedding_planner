import inspect
import json
from pathlib import Path
from typing import Union
from pydantic import BaseModel
from agents.prompts.types import LLMPromptInput

DATA_TYPES = Union[dict, str, BaseModel]


class BaseDataAssertionTest:
    """Base class for project tests."""

    # Set to True on a subclass to overwrite existing files in tests/data/
    overwrite_test_data: bool = False

    def assert_test_data(self, data: DATA_TYPES, file_name: str) -> DATA_TYPES:
        """
        Compare against saved test data, or create it on first run.
        Files are stored in ``data/`` next to the calling test module.
        Set ``overwrite_test_data = True`` on the test class to regenerate files.
        """

        caller_dir = Path(inspect.stack()[1].filename).parent
        test_data_dir = caller_dir / "data"
        test_data_dir.mkdir(parents=True, exist_ok=True)

        file_path = test_data_dir / self._snapshot_filename(data, file_name)
        expected = self._serialize(data)

        if self.overwrite_test_data or not file_path.exists():
            file_path.write_text(expected, encoding="utf-8")

        saved = file_path.read_text(encoding="utf-8")
        assert saved == expected, (
            f"Snapshot mismatch for {file_path.name}. "
            "Set overwrite_test_data = True to regenerate."
        )
        return data

    def _snapshot_filename(self, data: DATA_TYPES, file_name: str) -> str:
        """Return the snapshot file name for a given data type."""
        if isinstance(data, str):
            return f"{file_name}.txt"
        if isinstance(data, dict | BaseModel):
            return f"{file_name}.json"
        raise ValueError(f"Unsupported data type: {type(data)}")

    def _serialize(self, data: DATA_TYPES) -> str:
        """Convert test data to the string stored in snapshot files."""
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return json.dumps(data, indent=2)
        if isinstance(data, BaseModel):
            return data.model_dump_json(indent=2)
        raise ValueError(f"Unsupported data type: {type(data)}")


class PromptDataAssertionTest(BaseDataAssertionTest):
    """Base class for prompt tests."""

    def _snapshot_filename(self, data: DATA_TYPES, file_name: str) -> str:
        """Return the snapshot file name for a given data type."""
        if isinstance(data, LLMPromptInput):
            file_name = f"{file_name}.txt"
            return file_name
        filename = super()._snapshot_filename(data, file_name)
        return filename

    def _serialize(self, data: DATA_TYPES) -> str:
        """Convert test data to the string stored in snapshot files."""
        if isinstance(data, LLMPromptInput):
            serialized = self._format_llm_prompt_input(data)
            return serialized
        serialized = super()._serialize(data)
        return serialized

    @staticmethod
    def _format_llm_prompt_input(data) -> str:
        """Format the LLMPromptInput as a string."""
        formatted = f"{data.system}\n\n{data.user}"
        return formatted
