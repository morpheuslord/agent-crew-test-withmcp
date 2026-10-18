"""The migration command and the least-privilege application role."""

import uuid

import psycopg
import pytest

from taskboard import cli
from taskboard.dbadmin import ensure_app_role, libpq_url
from tests.integration.conftest import DATABASE_URL


def _app_url(role: str, password: str) -> str:
    assert DATABASE_URL
    base = libpq_url(DATABASE_URL)
    rest = base.split("@", 1)[1]
    return f"postgresql://{role}:{password}@{rest}"


def test_app_role_can_only_read_and_write_rows(migrated_db: str) -> None:
    role = f"tb_app_{uuid.uuid4().hex[:8]}"
    password = "app-role-password-123"
    ensure_app_role(migrated_db, password, role=role)
    ensure_app_role(migrated_db, password, role=role)  # idempotent
    with psycopg.connect(_app_url(role, password), autocommit=True) as conn:
        conn.execute("SELECT count(*) FROM users")
        conn.execute("SELECT count(*) FROM tasks")
        for statement in (
            "CREATE TABLE nope (id int)",
            "DROP TABLE comments",
            "ALTER TABLE users ADD COLUMN x int",
            "SELECT * FROM alembic_version",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(statement)


def test_app_role_input_is_validated(migrated_db: str) -> None:
    with pytest.raises(ValueError, match="role name"):
        ensure_app_role(migrated_db, "x" * 20, role="bad name; drop")
    with pytest.raises(ValueError, match="16 characters"):
        ensure_app_role(migrated_db, "short")


def test_migrate_command(migrated_db: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MIGRATION_DATABASE_URL", raising=False)
    assert cli.main(["migrate"]) == 2
    monkeypatch.setenv("MIGRATION_DATABASE_URL", migrated_db)
    monkeypatch.delenv("DB_APP_PASSWORD", raising=False)
    assert cli.main(["migrate"]) == 0
    monkeypatch.setenv("DB_APP_PASSWORD", "short")
    assert cli.main(["migrate"]) == 1
    monkeypatch.setenv("DB_APP_PASSWORD", "app-role-password-456")
    assert cli.main(["migrate"]) == 0
