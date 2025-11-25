from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from config import LOG_FILE, LOG_LEVEL

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def _ensure_log_path(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=None)
def get_logger(name: str = "ai_agent", level: Optional[str] = None) -> logging.Logger:
    """Configure and return an application logger."""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    resolved_level = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(resolved_level)

    formatter = logging.Formatter(LOG_FORMAT)
    log_path = Path(LOG_FILE)
    _ensure_log_path(log_path)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(resolved_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(resolved_level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger


__all__ = ["get_logger"]

