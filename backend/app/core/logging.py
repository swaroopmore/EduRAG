"""Logging helpers.

Logs carry operation, shortened ids, counts and timings - never passwords,
tokens, API keys or raw document text.
"""

from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.core.config import settings

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())
    # Third-party libraries are chatty.
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"edurag.{name}")


def short_id(value: Any) -> str:
    """First 8 characters of an id - enough to correlate, not to enumerate."""
    return str(value)[:8] if value else "-"


@contextmanager
def timed() -> Iterator[dict[str, float]]:
    """Context manager yielding a dict whose ``ms`` key is filled on exit."""
    result: dict[str, float] = {"ms": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["ms"] = round((time.perf_counter() - start) * 1000, 1)
