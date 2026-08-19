"""Application logging configuration shared by CLI and API execution."""

from __future__ import annotations

import logging
import os

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure console logs without replacing Uvicorn's own handlers."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format=LOG_FORMAT)
    logging.getLogger("app").setLevel(level)
