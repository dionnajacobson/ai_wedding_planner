"""HTTP request logging middleware."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from observability.logging import bind_request_id, clear_log_context

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request id and log request lifecycle events."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = bind_request_id(request.headers.get("X-Request-ID"))
        start = time.perf_counter()
        logger.info(
            "request_started",
            extra={"method": request.method, "path": request.url.path},
        )

        try:
            try:
                response = await call_next(request)
            except Exception:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.exception("request_failed", extra={"duration_ms": duration_ms})
                raise

            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request_completed",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_log_context()
