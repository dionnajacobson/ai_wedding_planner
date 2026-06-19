# AI Wedding Planner

Wedding planning chatbot powered by OpenAI, PostgreSQL, and Jinja prompts.

## Quick start

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker, OpenAI API key

```bash
cd ai_wedding_planner
uv sync
cp .env.example .env          # add OPENAI_API_KEY
docker compose up -d          # start PostgreSQL
uv run uvicorn api.main:app --reload
```

Open **http://127.0.0.1:8000** to chat. The UI saves your session in browser storage so refreshes keep the conversation.

API reference: **http://127.0.0.1:8000/docs**

## Terminal CLI

Prefer the command line?

```bash
uv run python cli.py
```

Each run creates a new session. Optional: `--first-name`, `--last-name`, `--email`.

## Configuration

| Variable | Required | Default |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | — |
| `DATABASE_URL` | No | `postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner` |

Inspect the database:

```bash
docker exec -it wedding_planner_db psql -U wedding -d wedding_planner
```

## Project layout

```
ai_wedding_planner/
├── api/           # FastAPI app, routes, web UI
├── cli.py         # Terminal chat
├── agents/        # Wedding agent + Jinja prompts
├── services/      # Business logic + DB stores
├── db/            # SQLAlchemy models
└── tests/         # Service and prompt tests
```

## Tests

```bash
uv run pytest
```

Prompt snapshot files live in `tests/agents/data/`. To regenerate after changing a template, set `overwrite_test_data = True` on the test class, run pytest, then set it back to `False`.

## Adding a prompt

1. Add a Jinja template in `agents/prompts/templates/`.
2. Add a prompt class in `agents/prompts/prompts.py`.
3. Add a snapshot test in `tests/agents/`.
