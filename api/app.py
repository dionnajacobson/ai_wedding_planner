from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import chat
from db.database import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables when the application starts."""
    init_db()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="AI Wedding Planner",
        description="Chat with your wedding planning assistant",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(chat.router)

    @app.get("/")
    def index() -> FileResponse:
        """Serve the chat web UI."""
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a simple liveness check for load balancers and monitoring."""
        return {"status": "ok"}

    return app


app = create_app()
