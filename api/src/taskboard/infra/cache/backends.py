"""Cache backends: Redis for deployments, in-memory for tests, and a no-op cache."""

import logging
import threading
import time

import redis

logger = logging.getLogger("taskboard.cache")


class RedisCache:
    """Redis-backed cache. Any Redis failure degrades to a miss or a no-op, never an error."""

    name = "redis"

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def get(self, key: str) -> str | None:
        try:
            value = self._client.get(key)
        except redis.RedisError:
            logger.warning("cache unavailable", extra={"op": "get"})
            return None
        return None if value is None else str(value)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            self._client.set(key, value, ex=ttl_seconds)
        except redis.RedisError:
            logger.warning("cache unavailable", extra={"op": "set"})

    def delete(self, *keys: str) -> None:
        if not keys:
            return
        try:
            self._client.delete(*keys)
        except redis.RedisError:
            logger.warning("cache unavailable", extra={"op": "delete"})

    def incr(self, key: str) -> int | None:
        try:
            return int(self._client.incr(key))
        except redis.RedisError:
            logger.warning("cache unavailable", extra={"op": "incr"})
            return None


class InMemoryCache:
    """Process-local cache with TTLs, for unit tests and single-process development."""

    name = "memory"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: dict[str, tuple[str, float | None]] = {}

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expires = entry
            if expires is not None and expires <= time.monotonic():
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._data[key] = (value, time.monotonic() + ttl_seconds)

    def delete(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._data.pop(key, None)

    def incr(self, key: str) -> int | None:
        with self._lock:
            current = int(self._data.get(key, ("0", None))[0]) + 1
            self._data[key] = (str(current), None)
            return current


class NullCache:
    """Caching disabled: every read misses and writes are ignored."""

    name = "none"

    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        return None

    def delete(self, *keys: str) -> None:
        return None

    def incr(self, key: str) -> int | None:
        return None
