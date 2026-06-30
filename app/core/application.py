"""
FastAPI application factory.

``create_app()`` assembles the application: middleware, CORS, routes, and
Swagger/OpenAPI metadata.  The Uvicorn entry point calls this function.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.settings import get_settings
from app.middleware.error_handler import ExceptionHandlerMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

logger = logging.getLogger("app.core")


def create_app() -> FastAPI:
    """Build and return the fully configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered Travel Reimbursement Approval Agent.  "
            "Evaluates employee travel claims against company policy using "
            "RAG-grounded reasoning and multi-tool orchestration."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # --- Middleware (order matters — outermost first) ---
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routes ---
    app.include_router(router, prefix="")

    # --- Startup event ---
    @app.on_event("startup")
    async def _startup() -> None:
        logger.info(
            "%s v%s starting [env=%s, provider=%s]",
            settings.app_name,
            settings.app_version,
            settings.app_env,
            settings.llm_provider,
        )
        # Pre-load FAISS index if it exists
        try:
            from app.rag.vector_store import get_vector_store

            store = get_vector_store()
            store.load_index()
            logger.info("FAISS index loaded at startup")
        except Exception as exc:
            logger.warning("FAISS index not available at startup: %s", exc)

    return app
