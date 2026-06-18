# AI Wedding Planner

An AI wedding planning assistant built with Python. The project renders structured LLM prompts from Jinja templates and will connect to external tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

## Overview

At a high level, the project has two main pieces:

1. **Prompt system** — Jinja templates define `system` and `user` blocks for LLM prompts. Subclasses of `JinjaPrompt` supply template context (couple names, wedding date, budget, etc.).
2. **MCP client** (`client.py`) — Entry point for connecting to MCP servers over SSE. This is early scaffolding for the interactive assistant.

```
ai_wedding_planner/
├── client.py                 # MCP client entry point
├── agents/
│   └── prompts/
│       ├── base.py           # Prompt ABC and JinjaPrompt renderer
│       ├── prompts.py        # Concrete prompt classes (base, wedding)
│       ├── templates/        # Jinja templates
│       │   ├── base.jinja
│       │   └── wedding_prompt.jinja
│       └── tests/            # Prompt snapshot tests
│           ├── test_prompts.py
│           └── data/         # Expected rendered output
└── tests/
    └── base.py               # Shared test helpers (snapshot assertions)
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Python 3.12+

## Setup

From the project root:

```bash
cd ai_wedding_planner
uv sync
```

This creates a virtual environment, installs runtime dependencies (`jinja2`, `mcp`, etc.), and dev dependencies (`pytest`).

## Running the project

Run the MCP client entry point (early scaffolding):

```bash
uv run python client.py
```

Try rendering a prompt directly (fully working today):

```bash
uv run python -c "from agents.prompts.prompts import WeddingPromptJinja; print(WeddingPromptJinja().render())"
```

## Running tests

Run the full test suite (pytest discovers all `test_*.py` files under the project root automatically):

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Run a single test file:

```bash
uv run pytest agents/prompts/tests/test_prompts.py
```

Run a single test by name:

```bash
uv run pytest agents/prompts/tests/test_prompts.py::TestWeddingPromptJinja::test_wedding_prompt_jinja_e2e
```

Filter tests by keyword:

```bash
uv run pytest -k wedding -v
```

### Snapshot tests

Prompt tests compare rendered output against files in `agents/prompts/tests/data/`. To regenerate snapshots after changing a template, temporarily set `overwrite_test_data = True` on the test class, run pytest, then set it back to `False`.

## Adding a new prompt

1. Create a template in `agents/prompts/templates/` that extends `base.jinja` and overrides the `system` and `user` blocks.
2. Add a subclass in `agents/prompts/prompts.py` with `template_name` and optional context in `__init__`.
3. Add a snapshot test in any `tests/test_*.py` file — pytest will pick it up automatically.
