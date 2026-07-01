---
paths:
  - "tests/**/*.py"
  - "**/test_*.py"
---

# Testing

## General

- Add a test for every new object (class, function); skip trivial passthroughs and cases that add no real coverage (e.g. asserting a class variable is set).
- Table-driven: `test_cases: list[dict[str, Any]]` with a `"name"` key, looped with `for case in test_cases:`; new scenarios are rows, not new methods.
- Three sections per test: `# ARRANGE`, `# ACT`, `# ASSERT`.
- No linting errors in test code.

## Mocks

- Only mock what you don't own: true external boundaries (DB, filesystem, third-party APIs, the LLM/MCP client) and non-deterministic/side-effecting code (time, email, payments) — keeps tests fast and non-flaky.
- Don't mock your own business logic/helpers — pass real inputs instead.
- Don't mock third-party types directly; wrap them in a thin internal adapter and mock that.
- Prefer a minimal hand-written fake over `unittest.mock`. More than ~3 mocks in one test is a smell that the unit does too much.
- Test behavior/outputs, not internal implementation steps.

## Paths

- Mirrors the source tree: `tests/agents/` ↔ `agents/`, `tests/services/` ↔ `services/`, named `test_<module>.py`.
- `tests/base.py` — shared base classes (e.g. `PromptDataAssertionTest` for prompt snapshots).
- `tests/conftest.py` — auto-applies the `non_api` marker to tests not marked `api`.
- `tests/agents/mock_data.py`, `tests/services/mock_data.py` — shared fixtures per package.
- Prompt snapshots live in a `data/` dir next to their test.
- E2E tests (hit real external APIs): suffix `_e2e.py`, marked `@pytest.mark.api`.
