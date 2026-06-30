"""
Enterprise-grade rotating log configuration.

Creates four separate log streams:
• **app.log**   — general application events
• **agent.log** — LLM / agent-specific traces
• **api.log**   — HTTP request/response logging
• **error.log** — ERROR+ across all loggers
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.config.settings import get_settings


def setup_logging() -> None:
    """Initialise the root logger and the four rotating file handlers."""
    settings = get_settings()
    log_dir = settings.project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger
    root = logging.getLogger()
    root.setLevel(log_level)

    # Prevent duplicate handlers on reload
    if root.handlers:
        return

    # Console handler (stdout)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(fmt)
    root.addHandler(console)

    # Rotating file handlers
    _files = {
        "app.log": logging.getLogger("app"),
        "agent.log": logging.getLogger("app.agents"),
        "api.log": logging.getLogger("app.api"),
    }
    for filename, logger in _files.items():
        handler = RotatingFileHandler(
            log_dir / filename,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        handler.setLevel(log_level)
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    # Dedicated error log — captures ERROR+ from all loggers
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(fmt)
    root.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger under the ``app`` hierarchy."""
    return logging.getLogger(f"app.{name}")
