# AI Wedding Planner

An AI wedding planning assistant built with Python, OpenAI, PostgreSQL, and Jinja prompt templates.

## Overview

The project includes:

1. **Prompt system** — Jinja templates define `system` and `user` blocks for LLM prompts.
2. **Wedding agent** — Loads conversation history, renders prompts, and calls OpenAI.
3. **Web UI** — FastAPI app with a browser chat interface (`api/`).
4. **Terminal CLI** — Interactive chat (`cli.py`).

```
ai_wedding_planner/
├── api/
│   ├── app.py                # FastAPI app factory
│   ├── main.py               # Uvicorn entry point
│   ├── routes/               # HTTP route handlers
│   └── static/               # Web chat UI
├── cli.py                    # Terminal chat client
├── agents/
│   ├── wedding_agent.py
│   └── prompts/
├── services/                 # Client, wedding, and message services
│   └── stores/
├── tests/
│   ├── agents/               # Prompt snapshot tests
│   └── services/             # Service unit tests
└── db/                       # SQLAlchemy models + PostgreSQL config
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.12+
- [Docker](https://docs.docker.com/get-docker/) (for PostgreSQL)
- OpenAI API key

## Setup

```bash
cd ai_wedding_planner
uv sync
cp .env.example .env
```

Add your OpenAI API key to `.env`, then start PostgreSQL:

```bash
docker compose up -d
```

## Running the web UI

```bash
uv run uvicorn api.main:app --reload
```

Open **http://127.0.0.1:8000** to chat. Enter your name and email to start, then share wedding details in the conversation. The UI saves your session in browser local storage so refreshes keep the conversation.

API docs: **http://127.0.0.1:8000/docs**

Chat endpoints:

- `POST /api/chat/start` — create a new session
- `POST /api/chat` — send a message and get the assistant reply
- `GET /api/chat/{session_id}/messages` — load conversation history

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

| Variable | Required | Default |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | — |
| `DATABASE_URL` | No | `postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner` |

Inspect the database:

```bash
docker exec -it wedding_planner_db psql -U wedding -d wedding_planner
```

## Running tests

```bash
uv run pytest
```

Run a specific file:

```bash
uv run pytest tests/agents/test_prompts.py
uv run pytest tests/services/test_message_service.py
```

Prompt snapshot files live in `tests/agents/data/`. To regenerate after changing a template, set `overwrite_test_data = True` on the test class, run pytest, then set it back to `False`.

## Adding a new prompt

1. Create a template in `agents/prompts/templates/` that extends `base.jinja` and overrides the `system` and `user` blocks.
2. Add a subclass in `agents/prompts/prompts.py` with `template_name` and optional context in `__init__`.
3. Add a snapshot test in `tests/agents/`.
