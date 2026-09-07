"""Logging configuration for the application."""

import logging
from typing import Final

from app.core.settings import get_settings


LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


def configure_logging() -> None:
    """Configure application-wide logging."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        force=True,
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a logger using the requested module name."""
    return logging.getLogger(name)