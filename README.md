# AI Wedding Planner

An AI wedding planning assistant built with Python, multi-provider LLM adapters, local tools (including Tavily web search), PostgreSQL, and Jinja prompt templates.

## Overview

The project includes:

1. **Prompt system** — Jinja templates render separate `system` and `user` blocks, including conversation history and tool results for the current turn.
2. **LLM client** — Provider adapters translate normalized requests to OpenAI (Responses API) or Anthropic (Messages API).
3. **Tool system** — Tools implement a shared `Tool` protocol, register in a `ToolRegistry`, and run asynchronously during agent turns.
4. **Wedding agent** — Loads history, renders prompts, loops on tool calls until the model responds, then saves messages.
5. **Web UI** — FastAPI app with a browser chat interface (`api/`).
6. **Terminal CLI** — Interactive async chat (`cli.py`).

```
ai_wedding_planner/
├── api/
│   ├── app.py                # FastAPI app factory
│   ├── main.py               # Uvicorn entry point
│   ├── routes/               # HTTP route handlers (chat)
│   └── static/               # Web chat UI
├── cli.py                    # Terminal chat client
├── agents/
│   ├── wedding_agent.py      # Chat loop + tool execution
│   ├── client/               # LLMClient, adapters, types, errors
│   ├── tools/                # Tool protocol, registry, web search
│   └── prompts/              # Jinja templates + prompt builders
├── observability/            # logging setup, request context, middleware
├── services/                 # Client, wedding, and message services
│   └── stores/
├── tests/
│   ├── agents/               # Prompt, adapter, tool tests
│   └── services/             # Service unit tests
└── db/                       # SQLAlchemy models + PostgreSQL config
```

## Architecture

```
User message
    ↓
WeddingAgent.chat (async)
    ↓
WeddingPromptJinja  →  system + user (history, query, tool_results)
    ↓
LLMClient.invoke  →  provider adapter (OpenAI or Anthropic)
    ↓
tool_calls?  ──yes──→  ToolRegistry.execute_all (async, concurrent)
    │                      ↓
    │                 re-render prompt with tool results
    │                      ↓
    └──────────────── loop (up to 10 rounds)
    ↓
Final assistant reply  →  MessageService
```

**Key design choices:**

- **Normalized LLM types** — `LLMRequest` / `LLMResponse` are provider-agnostic; adapters own format, call, and parse.
- **Injected adapters** — `LLMClient` receives a `Provider → LLMAdapter` registry (default: OpenAI + Anthropic).
- **Tool protocol** — Each tool implements `definition()` and `async execute()`; the registry routes by tool name.
- **Tool results vs history** — Tool output is rendered in the prompt for the current turn only; it is not stored as conversation history.
- **Plain enums** — `Model` and `Provider` are simple enums; no logic lives on enum classes.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.12+
- [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL)
- OpenAI API key (default model)
- Optional: Anthropic API key (adapter E2E tests), Tavily API key (web search)

## Setup

```bash
cd ai_wedding_planner
uv sync
cp .env.example .env
```

Add API keys to `.env`, then start services:

```bash
# Database only (local dev with uvicorn --reload on the host)
docker compose up -d db

# App + database (containerized API)
docker compose up --build
```

## Running the web UI

**Local development (hot reload):**

```bash
docker compose up -d db
uv run uvicorn api.main:app --reload
```

**Docker (app + db):**

```bash
docker compose up --build
```

Open **http://127.0.0.1:8000** to chat. Enter your name and email to start, then share wedding details in the conversation. The UI saves your session in browser local storage so refreshes keep the conversation.

API docs: **http://127.0.0.1:8000/docs**

Chat endpoints:

- `POST /api/chat/start` — create a new session
- `POST /api/chat` — send a message and get the assistant reply
- `GET /api/chat/{session_id}/messages` — load conversation history

LLM and tool errors map to HTTP status codes (401 auth, 429 rate limit, 502 provider errors).

## Running the terminal CLI

```bash
uv run python cli.py
```

Optional flags:

```bash
uv run python cli.py --first-name Alex --last-name Smith --email alex@example.com
```

Each CLI run creates a new session.

## Configuration

| Variable | Required | Default / notes |
|----------|----------|-----------------|
| `OPENAI_API_KEY` | Yes (default agent) | — |
| `ANTHROPIC_API_KEY` | No | For Anthropic adapter E2E tests |
| `TAVILY_API_KEY` | No | Required for live web search |
| `DATABASE_URL` | No | `postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner` |
| `LOG_LEVEL` | No | `INFO` |
| `LOG_FORMAT` | No | `console` locally; `json` in Docker |

### Models

`Model` values use the form `provider/model-id`:

| Enum | Value |
|------|-------|
| `GPT_4O_MINI_2024_07_18` | `openai/gpt-4o-mini-2024-07-18` |
| `CLAUDE_SONNET_4_6` | `anthropic/claude-sonnet-4-6` |

`WeddingAgent.default()` uses `GPT_4O_MINI_2024_07_18`. Pass a different `Model` when constructing the agent to switch providers.

Inspect the database:

```bash
docker exec -it wedding_planner_db psql -U wedding -d wedding_planner
```

## Observability

Uses Python [`logging`](https://docs.python.org/3/library/logging.html) + [structlog](https://www.structlog.org/) for structured JSON/console output.

| File | Purpose |
|------|---------|
| `logging.py` | `configure_logging()`, `log_context()` |
| `middleware.py` | Request id + HTTP lifecycle logs |

Call `configure_logging()` once at startup, then use `logging.getLogger(__name__)` in each module.

Every HTTP response includes an `X-Request-ID` header. Set `LOG_LEVEL` and `LOG_FORMAT` (`console` or `json`) via env vars.

View Docker logs:

```bash
docker compose logs -f app
```

## Tools

### Built-in tools

| Tool | Description | API |
|------|-------------|-----|
| `web_search` | Current wedding planning info (venues, vendors, pricing) | [Tavily](https://tavily.com/) |

### Adding a new tool

1. Create a class that implements `Tool` in `agents/tools/`:

```python
from agents.tools.protocols import Tool
from agents.tools.types import ToolCall, ToolDefinition, ToolResult

class MyTool(Tool):
    def definition(self) -> ToolDefinition:
        ...

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        ...
```

2. Register it when building the agent:

```python
tools = ToolRegistry()
tools.register(MyTool())
agent = WeddingAgent(..., tools=tools)
```

3. Add table-driven tests under `tests/agents/` (mocked unit tests + optional E2E with `@pytest.mark.skipif` when an API key is required).

Tool parameter schemas use Pydantic models; adapters convert them to provider-specific JSON Schema via `to_strict_json_schema`.

## LLM client

```python
from agents.client import LLMClient, Model
from agents.client.types import LLMRequest

client = LLMClient()
response = client.invoke(
    LLMRequest(
        system="You are a wedding planner.",
        user="Suggest venues in Austin.",
        model=Model.GPT_4O_MINI_2024_07_18,
        tools=tools.definitions(),  # optional
        max_tokens=1024,
    )
)
```

Adapters expose a single `invoke(LLMRequest) -> LLMResponse`. OpenAI uses `responses.create()`; Anthropic uses `messages.create()`.

## Running tests

```bash
uv run pytest
uv run ruff check .
```

Run a specific file:

```bash
uv run pytest tests/agents/test_prompts.py
uv run pytest tests/services/test_message_service.py
```

### Test layout

| Area | Files | Notes |
|------|-------|-------|
| Prompts | `tests/agents/test_prompts.py` | Snapshot tests in `tests/agents/data/` |
| LLM adapters | `tests/agents/test_adapter_e2e.py` | Live OpenAI/Anthropic; skipped without API keys |
| Tools | `tests/agents/test_web_search.py` | Mocked unit tests + live Tavily E2E |
| Tool registry | `tests/agents/test_tool_registry.py` | Registry routing |
| Services | `tests/services/` | Table-driven mocked service tests |

Tests use **classes with table-driven `test_cases`** (ARRANGE / ACT / ASSERT loops).

E2E tests skip automatically when keys are missing:

- `OPENAI_API_KEY` — OpenAI adapter E2E
- `ANTHROPIC_API_KEY` — Anthropic adapter E2E
- `TAVILY_API_KEY` — Tavily web search E2E

Prompt snapshot files live in `tests/agents/data/`. To regenerate after changing a template, set `overwrite_test_data = True` on the test class, run pytest, then set it back to `False`.

## Adding a new prompt

1. Create a template in `agents/prompts/templates/` that extends `base.jinja` and overrides the `system` and `user` blocks.
2. Add a subclass in `agents/prompts/prompts.py` with `template_name` and context in `__init__`.
3. Add a table-driven snapshot test in `tests/agents/test_prompts.py`.

The wedding prompt (`wedding_prompt.jinja`) includes:

- **Conversation history** — prior session messages as XML
- **Latest message** — the user's current query
- **Tool results** — XML from the current turn only (when tools have run)
