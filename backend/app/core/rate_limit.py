"""Tiny in-memory sliding-window rate limiter.

Good enough to blunt brute-force logins and runaway AI spend on a single
Railway instance.  For multi-instance deployments swap the store for Redis.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, Request

from app.auth.dependencies import get_current_user
from app.core.errors import RateLimitError
from app.models.user import User


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, max_calls: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= max_calls:
                raise RateLimitError()
            hits.append(now)
            # Opportunistic cleanup so the dict cannot grow without bound.
            if len(self._hits) > 10_000:
                for stale in [k for k, v in self._hits.items() if not v]:
                    self._hits.pop(stale, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def user_rate_limit(name: str, max_calls_getter, window_seconds: int = 60):
    """Dependency factory limiting an authenticated user per operation."""

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        limiter.check(f"{name}:{current_user.id}", max_calls_getter(), window_seconds)

    return dependency
