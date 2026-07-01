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

# Run tests without live external API calls (skips E2E tests needing credentials/network)
uv run pytest -m "not api"

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

`POST /api/chat` → `WeddingAgent.chat()` → builds an `Agent` with a sub-agent as a tool → `AgentRunner.run()` loops: render prompt → `LLMClient.invoke()` → if tool calls, `ToolOrchestrator.execute_all()` → repeat until text response → save messages. The FastAPI app (`api/app.py`) also serves a static chat + wedding-dashboard UI (`api/static/`) that consumes the chat routes in `api/routes/chat.py`, including `GET /api/chat/{session_id}/wedding` for the wedding profile.

### Agent framework layers

- **`agents/agent/types.py`** — `Agent` (config: model, prompt, tools, limits), `ToolEntry` (a prepared tool + optional sub-agent), `AgentRunResult`.
- **`agents/agent/agent.py`** — `AgentRunner` drives the tool loop. Each round re-renders the prompt with accumulated `ToolResult`s appended, then calls the LLM.
- **`agents/client/`** — `LLMClient` routes `LLMRequest` to provider adapters via `Provider` extracted from the model enum value (e.g. `"openai/gpt-4o-mini-2024-07-18"` → `OpenAIAdapter`). Both OpenAI and Anthropic adapters are registered by default.
- **`agents/tools/orchestrator.py`** — `ToolOrchestrator.prepare()` converts an `Agent`'s `tools=` list into `ToolEntry` objects. It handles three kinds of list members differently: `ToolDefinition` instances pass through as-is; `Agent` instances are wrapped into `AgentToolDefinition` entries (see below); `McpServer` instances are connected live and expanded into one `McpToolDefinition` per remote tool (see MCP tools below). On execution, sub-agent tool calls are routed to `AgentToolExecutor`, and MCP-prefixed tool calls are routed to `McpToolExecutor`.
- **`agents/prompts/`** — Jinja2 templates in `templates/`. Each template has `{% block system %}` and `{% block user %}` blocks. `JinjaPrompt.update_context()` accepts runtime values (tool results, tool descriptions) that are formatted and merged at render time via `runtime_fields`. Static context is set at construction; runtime context is cleared per turn by `AgentToolExecutor`.

### Sub-agent as tool pattern

Passing an `Agent` instance in the `tools=` list of another `Agent` causes `ToolOrchestrator.prepare()` to wrap it as an `AgentToolDefinition` (name: `agent_as_tool_{agent_name}`). When the LLM calls that tool, `AgentToolExecutor` updates the child agent's prompt with the `task` argument and runs it through the same `AgentRunner`. The child result is returned as a `ToolResult` to the parent.

### MCP tools

An `Agent`'s `tools=` list can also contain an `McpServer` (`agents/tools/mcp/config.py`; transports: `stdio`, `sse`, `streamable_http`), e.g. `ApifyMcpServer` in `agents/tools/mcp/apify.py`, which `agents/wedding_agent.py` passes to its vendor-search sub-agent. Unlike a normal `ToolDefinition`, an MCP server's tools aren't declared in code — `McpClientManager.connect_server()` (`agents/tools/mcp/client_manager.py`) opens a live session, calls `list_tools()`, and produces one `McpToolDefinition` per remote tool at prepare-time, with a provider-safe name (`mcp_{server_slug}_{tool_slug}`). All calls to any MCP tool route through the single shared `McpToolExecutor` → `McpClientManager.call_tool()`, which looks up the live session by formatted tool name. `McpClientManager` owns the connection lifecycle (`AsyncExitStack`) and is intentionally stateful — inject and reuse one instance rather than constructing it per call. The root `mcp.config.json` is gitignored/local and is not read by the app; MCP servers are wired up as Python `McpServer` values instead.

### Tool results and prompt context

Tool results accumulate across all rounds of a single `AgentRunner.run()` call and are re-injected into every subsequent prompt render via `format_tool_results_as_xml`. They are **not** stored in the DB — only the final user message and assistant reply are persisted via `MessageService`.

### Prompt snapshot tests

`tests/base.PromptDataAssertionTest` compares rendered prompts against `.txt` files in a `data/` directory next to the test. On first run (or when `overwrite_test_data = True`), files are generated. Set `overwrite_test_data = True` on the test class to regenerate snapshots after intentional prompt changes.

### Test markers

`pyproject.toml` defines `api` (calls a real external API — needs credentials/network) and `non_api` markers. `tests/conftest.py` auto-applies `non_api` to any test not explicitly marked `api`, so E2E tests (`test_adapter_e2e.py`, `test_apify_mcp_e2e.py`) are the only ones marked `api` and typically also `skipif` on a missing key. Use `uv run pytest -m "not api"` to skip them.

## Code conventions

From `.cursor/rules.mdc`:

- **Pydantic over dataclasses**; model attributes alphabetized. Only define the parameters actually needed by the current implementation.
- **Functions and methods alphabetized** within a file: public first, then private (`_`-prefixed).
- **Input arguments alphabetized**.
- **Always return named variables** (e.g. `return value` not `return data[key].item`).
- **Docstrings on every function and class**; comments explain *why*, not *what*; attribute comments go on the line above with `#`.
- **Inject stateless dependencies in `__init__`** (services, clients, runners); build stateful, per-request objects inside the method that uses them (e.g. `Agent`, prompt instances inside `chat()`).
- **Constants only when used multiple times** — prefer inline strings.
- **Imports stay at the top of the file** — never import inside functions or methods.
- **Table-driven unit tests**: `test_cases: list[dict[str, Any]]` with a `"name"` key; three sections `# ARRANGE`, `# ACT`, `# ASSERT`. Mock as little as possible.

## Configuration

| Variable | Notes |
|---|---|
| `OPENAI_API_KEY` | Required for default agent (`GPT_4O_MINI_2024_07_18`) |
| `ANTHROPIC_API_KEY` | Optional; required for Anthropic adapter E2E tests |
| `TAVILY_API_KEY` | Optional; required for live web search |
| `APIFY_API_TOKEN` | Optional; required for the Apify MCP vendor-search server and its E2E test |
| `DATABASE_URL` | Default: `postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner` |
| `LOG_LEVEL` / `LOG_FORMAT` | Default `INFO` / `console` (`json` in Docker) |

## Extending the system

**New tool:** Add `ToolName` in `agents/tools/types.py` → subclass `ToolDefinition` (schema) + implement `ToolExecutor` (logic) → register the executor in `ToolOrchestrator.default()` → add the `ToolDefinition` instance to the agent's `tools=` list.

**New MCP-backed tool:** No code needed per tool — define an `McpServer` (`agents/tools/mcp/config.py`) with its transport config and add it directly to an agent's `tools=` list; its tools are discovered at prepare-time.

**New prompt:** Add a Jinja template in `agents/prompts/templates/` → subclass `AgentJinjaPrompt` in `agents/prompts/prompts.py` → add snapshot test in `tests/agents/test_prompts.py`.

**New LLM model:** Add a value to `Model` enum in `agents/client/types.py` using `"provider/model-name"` format. If the provider is new, implement an `LLMAdapter` and register it in `LLMClient.default()`.
