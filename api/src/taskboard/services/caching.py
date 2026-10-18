"""Cache-aside reads and post-commit invalidation for the read-heavy paths.

Keys are built only from UUIDs and a SHA-256 digest of the filter, never from raw client text.
Values are JSON produced and parsed by Pydantic ``TypeAdapter``s. Authorization never relies on
cached data: callers check access against the database before or after reading the cache.
"""

import dataclasses
import hashlib
import json
import logging
import time
from collections.abc import Callable, Iterable
from typing import Final
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from taskboard.domain.entities import Page, Project, Task, TaskFilter, Team, User
from taskboard.infra.cache.base import Cache, CacheStats

logger = logging.getLogger("taskboard.cache")

PREFIX: Final = "tb:v1"

USER_ADAPTER: Final = TypeAdapter(User | None)
TEAM_LIST_ADAPTER: Final = TypeAdapter(list[Team])
PROJECT_LIST_ADAPTER: Final = TypeAdapter(list[Project])
TASK_ADAPTER: Final = TypeAdapter(Task | None)
TASK_PAGE_ADAPTER: Final = TypeAdapter(Page[Task])


class CacheKeys:
    """The single definition of every cache key."""

    @staticmethod
    def user(user_id: UUID) -> str:
        return f"{PREFIX}:user:{user_id}"

    @staticmethod
    def user_teams(user_id: UUID) -> str:
        return f"{PREFIX}:user:{user_id}:teams"

    @staticmethod
    def user_projects(user_id: UUID) -> str:
        return f"{PREFIX}:user:{user_id}:projects"

    @staticmethod
    def task(task_id: UUID) -> str:
        return f"{PREFIX}:task:{task_id}"

    @staticmethod
    def task_list_version(project_id: UUID) -> str:
        return f"{PREFIX}:project:{project_id}:tasks:ver"

    @staticmethod
    def task_list(project_id: UUID, version: str, flt: TaskFilter) -> str:
        canonical = json.dumps(dataclasses.asdict(flt), sort_keys=True, default=str)
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:32]
        return f"{PREFIX}:project:{project_id}:tasks:v{version}:{digest}"


class CacheAside:
    """Read-through helper with hit/miss accounting and post-commit invalidation."""

    def __init__(self, cache: Cache, stats: CacheStats, ttl_seconds: int) -> None:
        self._cache = cache
        self._stats = stats
        self._ttl = ttl_seconds

    @property
    def backend(self) -> str:
        return self._cache.name

    def stats(self) -> dict[str, dict[str, int]]:
        return self._stats.snapshot()

    def get_or_load[T](
        self, family: str, key: str, adapter: TypeAdapter[T], loader: Callable[[], T]
    ) -> T:
        raw = self._cache.get(key)
        if raw is not None:
            try:
                value = adapter.validate_json(raw)
            except ValidationError:
                # A malformed or outdated entry is treated as a miss and replaced.
                self._stats.record(family, "errors")
                logger.warning("cache entry discarded", extra={"family": family})
            else:
                self._stats.record(family, "hits")
                logger.debug("cache hit", extra={"family": family})
                return value
        self._stats.record(family, "misses")
        logger.debug("cache miss", extra={"family": family})
        value = loader()
        if value is not None:
            self._cache.set(key, adapter.dump_json(value).decode(), self._ttl)
        return value

    def task_list_version(self, project_id: UUID) -> str:
        return self._cache.get(CacheKeys.task_list_version(project_id)) or "0"

    # Invalidation, always called after the database commit.

    def forget_user(self, user_id: UUID) -> None:
        self._cache.delete(CacheKeys.user(user_id))

    def forget_user_teams(self, user_ids: Iterable[UUID]) -> None:
        self._cache.delete(*(CacheKeys.user_teams(u) for u in user_ids))

    def forget_user_projects(self, user_ids: Iterable[UUID]) -> None:
        self._cache.delete(*(CacheKeys.user_projects(u) for u in user_ids))

    def forget_task(self, task_id: UUID) -> None:
        self._cache.delete(CacheKeys.task(task_id))

    def forget_task_lists(self, project_id: UUID) -> None:
        """Make every cached page and filter combination of the project's task list unreachable."""
        key = CacheKeys.task_list_version(project_id)
        if self._cache.get(key) is None:
            # Start from a time-based value so a lost version key never reuses an old version.
            self._cache.set(key, str(time.time_ns()), self._ttl * 10)
        elif self._cache.incr(key) is None:
            logger.warning("task list version not bumped", extra={"project_id": str(project_id)})
