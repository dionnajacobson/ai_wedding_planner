import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv(override=True)

DEFAULT_DATABASE_URL = "postgresql+psycopg://wedding:wedding@localhost:5432/wedding_planner"


@lru_cache
def get_database_url() -> str:
    """Get the database URL."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
