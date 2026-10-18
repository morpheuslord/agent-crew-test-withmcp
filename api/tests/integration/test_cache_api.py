"""Caching against real Redis, and degraded operation without it."""

from pathlib import Path
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from taskboard.composition import Infrastructure, RequestServices
from taskboard.config import Settings
from taskboard.main import create_app
from tests.integration.conftest import Api, make_settings


def test_reads_are_cached_and_writes_invalidate(api: Api) -> None:
    _, token = api.user("olive")
    team = api.call("POST", "/teams", token, json={"name": "Core"}).json()
    project = api.call("POST", f"/teams/{team['id']}/projects", token, json={"name": "B"}).json()
    task = api.call("POST", f"/projects/{project['id']}/tasks", token, json={"title": "Old"}).json()
    for _ in range(2):
        assert api.call("GET", f"/tasks/{task['id']}", token).json()["title"] == "Old"
        api.call("GET", f"/projects/{project['id']}/tasks", token)
        api.call("GET", "/teams", token)
    api.call("PATCH", f"/tasks/{task['id']}", token, json={"title": "New"})
    assert api.call("GET", f"/tasks/{task['id']}", token).json()["title"] == "New"
    listed = api.call("GET", f"/projects/{project['id']}/tasks", token).json()
    assert listed["items"][0]["title"] == "New"


def test_cache_stats_endpoint(api: Api) -> None:
    infra: Infrastructure = cast(FastAPI, api.client.app).state.infra
    with infra.session_factory() as session:
        RequestServices(infra, session).provisioner.ensure_admin(
            "root@example.test", "root-password-123"
        )
    admin_token = api.login("root", "root-password-123")
    _, token = api.user("mo")
    assert api.call("GET", "/admin/cache/stats", token).status_code == 403
    for _ in range(3):
        api.call("GET", "/auth/me", token)
    stats = api.call("GET", "/admin/cache/stats", admin_token).json()
    assert stats["backend"] == "redis"
    assert stats["families"]["user"]["hits"] >= 2


def test_api_keeps_working_without_redis(settings: Settings, tmp_path: Path) -> None:
    no_redis = make_settings(tmp_path / "files", redis_url="redis://127.0.0.1:1/0")
    with TestClient(create_app(no_redis)) as client:
        api = Api(client)
        ready = client.get("/readyz").json()
        assert ready["status"] == "ready"
        assert ready["checks"]["redis"] == "degraded"
        _, token = api.user("ada")
        team = api.call("POST", "/teams", token, json={"name": "Core"}).json()
        assert [t["id"] for t in api.call("GET", "/teams", token).json()] == [team["id"]]
        assert api.call("GET", "/auth/me", token).status_code == 200
