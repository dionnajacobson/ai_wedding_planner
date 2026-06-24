# AI Wedding Planner

Wedding planning assistant: FastAPI web UI, terminal CLI, Jinja prompts, OpenAI/Anthropic adapters, Tavily web search, PostgreSQL.

## Quick start

**Prerequisites:** [uv](https://docs.astral.sh/uv/), Python 3.12+, Docker, `OPENAI_API_KEY`

```bash
cd ai_wedding_planner
uv sync
cp .env.example .env   # add API keys
docker compose up -d db
uv run uvicorn api.main:app --reload
```

Open **http://127.0.0.1:8000** (API docs at `/docs`). Or run the CLI: `uv run python cli.py`

Full stack in Docker: `docker compose up --build`

## Layout

```
agents/     wedding_agent, agent runner, LLM client, tools, prompts
api/        FastAPI app + web chat UI
services/   message + wedding services
db/         SQLAlchemy + PostgreSQL
observability/  structlog + request middleware
tests/
```

## Flow

`WeddingAgent.chat` → render prompt → `AgentRunner` loops on LLM calls → `ToolRegistry` runs tool calls → save reply.

Tool **definitions** (`ToolDefinition` on the agent) and **executors** (`ToolRegistry.register(ToolName, ...)`) are linked by name only. Tool results appear in the prompt for the current turn, not in stored history.

## Configuration

| Variable | Notes |
|----------|-------|
| `OPENAI_API_KEY` | Required for default agent |
| `ANTHROPIC_API_KEY` | Optional; adapter E2E tests |
| `TAVILY_API_KEY` | Optional; live web search |
| `DATABASE_URL` | Default: `postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner` |
| `LOG_LEVEL` / `LOG_FORMAT` | Default `INFO` / `console` (`json` in Docker) |

Default model: `GPT_4O_MINI_2024_07_18`. Also supported: `CLAUDE_SONNET_4_6`.

## API

- `POST /api/chat/start`
- `POST /api/chat`
- `GET /api/chat/{session_id}/messages`

## Adding a tool

1. Add `ToolName` in `agents/tools/types.py`
2. Subclass `ToolDefinition` + implement `ToolExecutor`
3. `registry.register(ToolName.MY_TOOL, MyToolExecutor())` and `Agent(..., tools=[MyToolDefinition()])`
4. Tests in `tests/agents/` (table-driven; E2E skipped without API keys)

Built-in: `WEB_SEARCH` (Tavily) — `WebSearchDefinition()` on the agent, executor in `ToolRegistry.default()`.

## Adding a prompt

Template in `agents/prompts/templates/` → subclass in `agents/prompts/prompts.py` → snapshot test in `tests/agents/test_prompts.py`.

## Tests

```bash
uv run pytest
uv run ruff check .
```

Table-driven tests under `tests/agents/` and `tests/services/`. E2E tests skip when API keys are missing.
