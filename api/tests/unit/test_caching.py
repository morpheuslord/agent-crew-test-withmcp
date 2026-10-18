"""Cache-aside behaviour, invalidation and degradation."""

import json
from datetime import timedelta
from uuid import uuid4

import pytest
import redis
from pydantic import TypeAdapter

from taskboard.domain.entities import TaskChanges, TaskDraft, TaskFilter
from taskboard.domain.enums import Role, TaskStatus
from taskboard.domain.errors import (
    AuthenticationRequiredError,
    NotFoundError,
    PermissionDeniedError,
)
from taskboard.infra.cache.backends import InMemoryCache, NullCache, RedisCache
from taskboard.infra.cache.base import CacheStats
from taskboard.services.caching import USER_ADAPTER, CacheAside, CacheKeys
from taskboard.services.security import hash_token
from tests.unit.conftest import World

INT_LIST = TypeAdapter(list[int])


def test_get_or_load_counts_hits_and_misses_and_stores_json() -> None:
    backend = InMemoryCache()
    cache = CacheAside(backend, CacheStats(), 60)
    calls: list[int] = []

    def load() -> list[int]:
        calls.append(1)
        return [1, 2, 3]

    assert cache.get_or_load("nums", "k", INT_LIST, load) == [1, 2, 3]
    assert cache.get_or_load("nums", "k", INT_LIST, load) == [1, 2, 3]
    assert calls == [1]
    assert json.loads(backend.get("k") or "") == [1, 2, 3]
    assert cache.stats() == {"nums": {"hits": 1, "misses": 1, "errors": 0}}
    assert cache.backend == "memory"


def test_malformed_entries_are_discarded() -> None:
    backend = InMemoryCache()
    backend.set("k", '{"not": "a list"}', 60)
    cache = CacheAside(backend, CacheStats(), 60)
    assert cache.get_or_load("nums", "k", INT_LIST, lambda: [7]) == [7]
    assert cache.stats()["nums"]["errors"] == 1
    assert backend.get("k") == "[7]"


def test_task_list_versions_change_keys() -> None:
    backend = InMemoryCache()
    cache = CacheAside(backend, CacheStats(), 60)
    project_id = uuid4()
    assert cache.task_list_version(project_id) == "0"
    cache.forget_task_lists(project_id)
    first = cache.task_list_version(project_id)
    assert int(first) > 1_000_000
    cache.forget_task_lists(project_id)
    assert int(cache.task_list_version(project_id)) == int(first) + 1
    a = CacheKeys.task_list(project_id, "1", TaskFilter(page=1))
    b = CacheKeys.task_list(project_id, "1", TaskFilter(page=2))
    c = CacheKeys.task_list(project_id, "2", TaskFilter(page=1))
    assert len({a, b, c}) == 3
    assert "page" not in a


def test_in_memory_entries_expire(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [10.0]
    monkeypatch.setattr("taskboard.infra.cache.backends.time.monotonic", lambda: now[0])
    backend = InMemoryCache()
    backend.set("k", "v", 5)
    assert backend.get("k") == "v"
    now[0] = 16.0
    assert backend.get("k") is None
    assert backend.incr("n") == 1
    backend.delete("n")
    assert backend.get("n") is None


def test_redis_failures_degrade_to_misses() -> None:
    broken = redis.Redis(host="127.0.0.1", port=1, socket_connect_timeout=0.05)
    backend = RedisCache(broken)
    assert backend.get("k") is None
    backend.set("k", "v", 5)
    backend.delete("k")
    backend.delete()
    assert backend.incr("k") is None
    cache = CacheAside(backend, CacheStats(), 60)
    assert cache.get_or_load("nums", "k", INT_LIST, lambda: [1]) == [1]
    cache.forget_task_lists(uuid4())


def test_null_cache_never_hits() -> None:
    cache = CacheAside(NullCache(), CacheStats(), 60)
    assert cache.get_or_load("nums", "k", INT_LIST, lambda: [1]) == [1]
    assert cache.get_or_load("nums", "k", INT_LIST, lambda: [2]) == [2]
    assert cache.stats()["nums"]["misses"] == 2
    cache.forget_task_lists(uuid4())


def test_team_and_project_lists_follow_membership(world: World) -> None:
    owner = world.user("olive")
    member = world.user("mo")
    assert world.teams.list_my_teams(member) == []
    assert world.projects.list_my_projects(member) == []
    team = world.teams.create_team(owner, "Core")
    project = world.projects.create(owner, team.id, "Board", None)
    world.teams.add_member(owner, team.id, member.email)
    assert [t.id for t in world.teams.list_my_teams(member)] == [team.id]
    assert [p.id for p in world.projects.list_my_projects(member)] == [project.id]
    world.projects.update(owner, project.id, name="Renamed", webhook_url=None, clear_webhook=False)
    assert world.projects.list_my_projects(member)[0].name == "Renamed"
    world.teams.remove_member(owner, team.id, member.id)
    assert world.teams.list_my_teams(member) == []
    assert world.projects.list_my_projects(member) == []


def test_task_cache_never_bypasses_membership(world: World) -> None:
    owner = world.user("olive")
    member = world.user("mo")
    team = world.teams.create_team(owner, "Core")
    world.teams.add_member(owner, team.id, member.email)
    project = world.projects.create(owner, team.id, "Board", None)
    task = world.tasks.create(member, project.id, TaskDraft(title="Cached"))
    assert world.tasks.get(member, task.id).title == "Cached"
    assert world.tasks.get(member, task.id).title == "Cached"
    assert world.cache.stats()["task"]["hits"] == 1
    world.teams.remove_member(owner, team.id, member.id)
    with pytest.raises(NotFoundError):
        world.tasks.get(member, task.id)
    with pytest.raises(NotFoundError):
        world.tasks.get(member, uuid4())


def test_task_writes_invalidate_detail_and_lists(world: World) -> None:
    owner = world.user("olive")
    team = world.teams.create_team(owner, "Core")
    project = world.projects.create(owner, team.id, "Board", None)
    task = world.tasks.create(owner, project.id, TaskDraft(title="Old"))
    assert world.tasks.list_project_tasks(owner, project.id, TaskFilter()).total == 1
    world.tasks.update(owner, task.id, TaskChanges(title="New", status=TaskStatus.DONE))
    assert world.tasks.get(owner, task.id).title == "New"
    assert world.tasks.list_project_tasks(owner, project.id, TaskFilter()).items[0].title == "New"
    world.tasks.create(owner, project.id, TaskDraft(title="Second"))
    assert world.tasks.list_project_tasks(owner, project.id, TaskFilter()).total == 2
    world.tasks.delete(owner, task.id)
    assert world.tasks.list_project_tasks(owner, project.id, TaskFilter()).total == 1
    with pytest.raises(NotFoundError):
        world.tasks.get(owner, task.id)


def test_profile_cache_follows_admin_changes(world: World) -> None:
    admin = world.user("root", Role.ADMIN)
    world.auth.register("ada@example.test", "Ada", "correct-horse-battery", "10.0.0.1")
    session = world.auth.login("ada@example.test", "correct-horse-battery", "10.0.0.1")
    assert world.auth.authenticate(session.token).role is Role.MEMBER
    world.admin.update_user(admin, session.user.id, role=Role.ADMIN, is_active=None)
    assert world.auth.authenticate(session.token).role is Role.ADMIN
    # Even if a session row survived, a deactivated profile is refused.
    world.admin.update_user(admin, session.user.id, role=None, is_active=False)
    later = world.clock.now() + timedelta(hours=1)
    world.store.sessions[hash_token(session.token)] = (session.user.id, later)
    with pytest.raises(AuthenticationRequiredError):
        world.auth.authenticate(session.token)


def test_stale_cached_role_never_grants_access(world: World) -> None:
    """F-080: simulate the race by writing an admin profile back after the demotion."""
    admin = world.user("root", Role.ADMIN)
    world.auth.register("ada@example.test", "Ada", "correct-horse-battery", "10.0.0.1")
    session = world.auth.login("ada@example.test", "correct-horse-battery", "10.0.0.1")
    world.admin.update_user(admin, session.user.id, role=Role.ADMIN, is_active=None)
    stale = world.auth.authenticate(session.token)
    assert stale.role is Role.ADMIN
    world.admin.update_user(admin, session.user.id, role=Role.MEMBER, is_active=None)
    backend_key = CacheKeys.user(session.user.id)
    world.cache.get_or_load("user", backend_key, USER_ADAPTER, lambda: stale)
    assert world.auth.authenticate(session.token).role is Role.MEMBER
    with pytest.raises(PermissionDeniedError):
        world.admin.list_users(world.auth.authenticate(session.token), 1, 10)


def test_cache_stats_are_admin_only(world: World) -> None:
    with pytest.raises(PermissionDeniedError):
        world.admin.cache_stats(world.user("mo"))
    stats = world.admin.cache_stats(world.user("root", Role.ADMIN))
    assert stats["backend"] == "memory"
