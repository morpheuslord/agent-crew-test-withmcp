"""Cache interface and hit/miss statistics."""

import threading
from typing import Protocol


class Cache(Protocol):
    """A string key-value store. Values are JSON text; nothing is ever pickled."""

    name: str

    def get(self, key: str) -> str | None: ...

    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

    def delete(self, *keys: str) -> None: ...

    def incr(self, key: str) -> int | None:
        """Atomically increment a counter; ``None`` if the backend is unavailable."""
        ...


class CacheStats:
    """Thread-safe hit/miss counters per key family, readable from the admin stats endpoint."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: dict[str, dict[str, int]] = {}

    def record(self, family: str, outcome: str) -> None:
        with self._lock:
            family_counts = self._counts.setdefault(family, {"hits": 0, "misses": 0, "errors": 0})
            family_counts[outcome] += 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {family: dict(counts) for family, counts in self._counts.items()}
