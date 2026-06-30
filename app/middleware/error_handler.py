"""
Global exception handler middleware for FastAPI.

Catches application-specific exceptions (``AgentBaseError`` and subclasses)
as well as unhandled exceptions, and returns a consistent JSON error envelope.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.exceptions import AgentBaseError

logger = logging.getLogger("app.middleware")


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Convert any unhandled exception into a uniform JSON error response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except AgentBaseError as exc:
            logger.warning("Application error [%d]: %s", exc.status_code, exc.message)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": type(exc).__name__,
                    "detail": exc.message,
                    "status_code": exc.status_code,
                },
            )
        except Exception as exc:
            logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "detail": "An unexpected error occurred. Please try again later.",
                    "status_code": 500,
                },
            )
