"""Integration fixtures: the real app against real PostgreSQL and Redis.

Set ``TEST_DATABASE_URL`` and ``TEST_REDIS_URL`` (``make test`` and CI do). The schema is built
with the Alembic migrations, so the tests also prove the migrations match the models.
"""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import redis
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine

from taskboard.config import Environment, Settings
from taskboard.main import create_app
from taskboard.models.tables import Base

API_ROOT = Path(__file__).resolve().parents[2]
SERVICE_SECRET = "integration-service-secret-0123456789"
PASSWORD = "correct-horse-battery"

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
REDIS_URL = os.environ.get("TEST_REDIS_URL")

pytestmark = pytest.mark.integration


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if DATABASE_URL and REDIS_URL:
        return
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL and TEST_REDIS_URL are not set")
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def migrated_db() -> str:
    assert DATABASE_URL
    os.environ["MIGRATION_DATABASE_URL"] = DATABASE_URL
    config = Config(str(API_ROOT / "alembic.ini"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return DATABASE_URL


def make_settings(storage_path: Path, **overrides: Any) -> Settings:
    assert DATABASE_URL
    values: dict[str, Any] = {
        "environment": Environment.TEST,
        "database_url": DATABASE_URL,
        "redis_url": REDIS_URL,
        "service_auth_secret": SERVICE_SECRET,
        "webhook_signing_secret": "integration-webhook-secret-0123456789",
        "public_base_url": "http://localhost:3000",
        "storage_local_path": str(storage_path),
        "max_upload_bytes": 4096,
        "log_level": "DEBUG",
    }
    values.update(overrides)
    return Settings(**values)


@dataclass
class Api:
    """Thin helper that adds the service header and an optional bearer token."""

    client: TestClient

    def call(self, method: str, path: str, token: str | None = None, **kwargs: Any) -> Response:
        headers = {"X-Service-Token": SERVICE_SECRET, **kwargs.pop("headers", {})}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response: Response = self.client.request(
            method, f"/api/v1{path}", headers=headers, **kwargs
        )
        return response

    def register(self, name: str) -> dict[str, Any]:
        response = self.call(
            "POST",
            "/auth/register",
            json={
                "email": f"{name}@example.test",
                "display_name": name.title(),
                "password": PASSWORD,
            },
        )
        assert response.status_code == 201, response.text
        user: dict[str, Any] = response.json()
        return user

    def login(self, name: str, password: str = PASSWORD) -> str:
        response = self.call(
            "POST", "/auth/login", json={"email": f"{name}@example.test", "password": password}
        )
        assert response.status_code == 200, response.text
        token: str = response.json()["token"]
        return token

    def user(self, name: str) -> tuple[dict[str, Any], str]:
        return self.register(name), self.login(name)


def _clean(database_url: str) -> None:
    engine = create_engine(database_url)
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    engine.dispose()
    if REDIS_URL:
        redis.Redis.from_url(REDIS_URL).flushdb()


@pytest.fixture
def settings(migrated_db: str, tmp_path: Path) -> Settings:
    _clean(migrated_db)
    return make_settings(tmp_path / "attachments")


@pytest.fixture
def api(settings: Settings) -> Iterator[Api]:
    with TestClient(create_app(settings)) as client:
        yield Api(client)
