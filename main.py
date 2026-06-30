"""
Travel Reimbursement Approval Agent — Application Entry Point.

Starts the FastAPI server via Uvicorn with settings loaded from
environment variables and config.ini.
"""

import uvicorn

from app.config.settings import get_settings
from app.utils.logging_config import setup_logging


def main() -> None:
    """Bootstrap logging and launch the Uvicorn ASGI server."""
    setup_logging()
    settings = get_settings()

    uvicorn.run(
        "app.core.application:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
