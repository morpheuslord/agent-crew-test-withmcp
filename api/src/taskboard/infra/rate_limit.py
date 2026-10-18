"""Fixed-window counters for login and email throttling."""

import hashlib
import logging
import threading
import time
from typing import Protocol

import redis

logger = logging.getLogger("taskboard.ratelimit")


def limiter_key(scope: str, value: str) -> str:
    """Hash identifying values (emails, IPs) so they never appear in Redis key names."""
    digest = hashlib.sha256(value.lower().encode("utf-8")).hexdigest()[:32]
    return f"rl:{scope}:{digest}"


class RateLimiter(Protocol):
    def hit(self, key: str, window_seconds: int) -> int:
        """Increment the counter for ``key`` and return the new count in the current window."""
        ...

    def count(self, key: str) -> int: ...

    def reset(self, key: str) -> None: ...


class InMemoryRateLimiter:
    """Per-process limiter, used in tests and as the fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[int, float]] = {}

    def _live(self, key: str, now: float) -> tuple[int, float] | None:
        entry = self._entries.get(key)
        if entry is None or entry[1] <= now:
            self._entries.pop(key, None)
            return None
        return entry

    def hit(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        with self._lock:
            entry = self._live(key, now)
            count, expires = entry if entry else (0, now + window_seconds)
            self._entries[key] = (count + 1, expires)
            return count + 1

    def count(self, key: str) -> int:
        with self._lock:
            entry = self._live(key, time.monotonic())
            return entry[0] if entry else 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)


class RedisRateLimiter:
    """Redis-backed counters shared by all API instances, falling back to in-process counters."""

    def __init__(self, client: redis.Redis, fallback: InMemoryRateLimiter) -> None:
        self._client = client
        self._fallback = fallback

    def hit(self, key: str, window_seconds: int) -> int:
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds, nx=True)
            count, _ = pipe.execute()
            return int(count)
        except redis.RedisError:
            logger.warning("rate limiter falling back to memory", extra={"op": "hit"})
            return self._fallback.hit(key, window_seconds)

    def count(self, key: str) -> int:
        try:
            value = self._client.get(key)
            return int(str(value)) if value is not None else 0
        except redis.RedisError:
            logger.warning("rate limiter falling back to memory", extra={"op": "count"})
            return self._fallback.count(key)

    def reset(self, key: str) -> None:
        try:
            self._client.delete(key)
        except redis.RedisError:
            logger.warning("rate limiter falling back to memory", extra={"op": "reset"})
        self._fallback.reset(key)
