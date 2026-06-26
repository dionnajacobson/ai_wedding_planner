# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start the database
docker compose up -d db

# Run the API server
uv run uvicorn api.main:app --reload

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/agents/test_agent.py

# Run a single test by name
uv run pytest tests/agents/test_agent.py::TestAgent::test_run

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## Architecture

This is a multi-agent wedding planning assistant built on a custom agent framework (not LangChain/OpenAI Agents SDK). The framework lives entirely in `agents/`.

### Request flow

`POST /api/chat` → `WeddingAgent.chat()` → builds an `Agent` with a sub-agent as a tool → `AgentRunner.run()` loops: render prompt → `LLMClient.invoke()` → if tool calls, `ToolOrchestrator.execute_all()` → repeat until text response → save messages.

### Agent framework layers

- **`agents/agent/types.py`** — `Agent` (config: model, prompt, tools, limits), `ToolEntry` (a prepared tool + optional sub-agent), `AgentRunResult`.
- **`agents/agent/agent.py`** — `AgentRunner` drives the tool loop. Each round re-renders the prompt with accumulated `ToolResult`s appended, then calls the LLM.
- **`agents/client/`** — `LLMClient` routes `LLMRequest` to provider adapters via `Provider` extracted from the model enum value (e.g. `"openai/gpt-4o-mini-2024-07-18"` → `OpenAIAdapter`). Both OpenAI and Anthropic adapters are registered by default.
- **`agents/tools/orchestrator.py`** — `ToolOrchestrator.prepare()` converts `Agent` objects in a tool list into `AgentToolDefinition` entries. On execution, sub-agent tool calls are routed to `AgentToolExecutor`, which runs the child agent through the same runner.
- **`agents/prompts/`** — Jinja2 templates in `templates/`. Each template has `{% block system %}` and `{% block user %}` blocks. `JinjaPrompt.update_context()` accepts runtime values (tool results, tool descriptions) that are formatted and merged at render time via `runtime_fields`. Static context is set at construction; runtime context is cleared per turn by `AgentToolExecutor`.

### Sub-agent as tool pattern

Passing an `Agent` instance in the `tools=` list of another `Agent` causes `ToolOrchestrator.prepare()` to wrap it as an `AgentToolDefinition` (name: `agent_as_tool_{agent_name}`). When the LLM calls that tool, `AgentToolExecutor` updates the child agent's prompt with the `task` argument and runs it through the same `AgentRunner`. The child result is returned as a `ToolResult` to the parent.

### Tool results and prompt context

Tool results accumulate across all rounds of a single `AgentRunner.run()` call and are re-injected into every subsequent prompt render via `format_tool_results_as_xml`. They are **not** stored in the DB — only the final user message and assistant reply are persisted via `MessageService`.

### Prompt snapshot tests

`tests/base.PromptDataAssertionTest` compares rendered prompts against `.txt` files in a `data/` directory next to the test. On first run (or when `overwrite_test_data = True`), files are generated. Set `overwrite_test_data = True` on the test class to regenerate snapshots after intentional prompt changes.

## Code conventions

From `.cursor/rules.mdc`:

- **Pydantic over dataclasses**; model attributes alphabetized.
- **Functions and methods alphabetized** within a file: public first, then private (`_`-prefixed).
- **Input arguments alphabetized**.
- **Always return named variables** (e.g. `return value` not `return data[key].item`).
- **Docstrings on every function and class**; comments explain *why*, not *what*.
- **Inject stateless dependencies in `__init__`** (services, clients, runners); build stateful, per-request objects inside the method that uses them (e.g. `Agent`, prompt instances inside `chat()`).
- **Constants only when used multiple times** — prefer inline strings.
- **Table-driven unit tests**: `test_cases: list[dict[str, Any]]` with a `"name"` key; three sections `# ARRANGE`, `# ACT`, `# ASSERT`.

## Configuration

| Variable | Notes |
|---|---|
| `OPENAI_API_KEY` | Required for default agent (`GPT_4O_MINI_2024_07_18`) |
| `ANTHROPIC_API_KEY` | Optional; required for Anthropic adapter E2E tests |
| `TAVILY_API_KEY` | Optional; required for live web search |
| `DATABASE_URL` | Default: `postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner` |
| `LOG_LEVEL` / `LOG_FORMAT` | Default `INFO` / `console` (`json` in Docker) |

## Extending the system

**New tool:** Add `ToolName` in `agents/tools/types.py` → subclass `ToolDefinition` (schema) + implement `ToolExecutor` (logic) → register the executor in `ToolOrchestrator.default()` → add the `ToolDefinition` instance to the agent's `tools=` list.

**New prompt:** Add a Jinja template in `agents/prompts/templates/` → subclass `AgentJinjaPrompt` in `agents/prompts/prompts.py` → add snapshot test in `tests/agents/test_prompts.py`.

**New LLM model:** Add a value to `Model` enum in `agents/client/types.py` using `"provider/model-name"` format. If the provider is new, implement an `LLMAdapter` and register it in `LLMClient.default()`.
