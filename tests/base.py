import inspect
import json
from pathlib import Path


class BaseDataAssertionTest:
    """Base class for project tests."""

    # Set to True on a subclass to overwrite existing files in tests/data/
    overwrite_test_data: bool = False

    def assert_test_data(self, data: dict | str, file_name: str) -> dict | str:
        """
        Compare against saved test data, or create it on first run.
        Files are stored in ``data/`` next to the calling test module.
        Set ``overwrite_test_data = True`` on the test class to regenerate files.
        """

        caller_dir = Path(inspect.stack()[1].filename).parent
        test_data_dir = caller_dir / "data"
        test_data_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(data, dict):
            file_path = test_data_dir / f"{file_name}.json"
        elif isinstance(data, str):
            file_path = test_data_dir / f"{file_name}.txt"
        else:
            raise ValueError(f"Invalid data type: {type(data)}")

        if self.overwrite_test_data or not file_path.exists():
            self._write_test_data(file_path, data)

        saved_data = self._read_test_data(file_path, type(data))
        assert saved_data == data
        return data
        
    @staticmethod
    def _read_test_data(file_path: Path, data_type: type) -> dict | str:
        """Read the test data from a file."""
        data = file_path.read_text(encoding="utf-8")
        if data_type is dict:
            data = json.loads(data)
        return data    

    @staticmethod
    def _write_test_data(file_path: Path, data: dict | str) -> None:
        """Write the test data to a file."""
        if isinstance(data, dict):
            file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            file_path.write_text(data, encoding="utf-8")

