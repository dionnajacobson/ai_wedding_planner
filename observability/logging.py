"""Logging setup and request-scoped context helpers."""

from __future__ import annotations

import logging
import os
import sys
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, unbind_contextvars

_configured = False


def configure_logging() -> None:
    """Configure stdlib logging with structlog processors (idempotent)."""
    global _configured
    if _configured:
        return

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    log_format = os.getenv("LOG_FORMAT", "console").lower()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if log_format == "json"
        else structlog.dev.ConsoleRenderer()
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _configured = True


def bind_request_id(request_id: str | None = None) -> str:
    """Bind a request id to the current log context."""
    bound_request_id = request_id or str(uuid.uuid4())
    bind_contextvars(request_id=bound_request_id)
    return bound_request_id


def clear_log_context() -> None:
    """Clear all bound log context variables."""
    clear_contextvars()


@contextmanager
def log_context(**fields: Any) -> Generator[None, None, None]:
    """Bind temporary fields (e.g. session_id) for a block."""
    bind_contextvars(**fields)
    try:
        yield
    finally:
        unbind_contextvars(*fields.keys())
