"""Uvicorn entry point: ``uv run uvicorn api.main:app --reload``."""

from api.app import app

__all__ = ["app"]
