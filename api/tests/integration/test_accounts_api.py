"""Accounts, sessions, admin and the management command, end to end."""

from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import create_engine, select

from taskboard import cli
from taskboard.config import Settings, get_settings
from taskboard.models.tables import OutboxRow
from tests.integration.conftest import PASSWORD, SERVICE_SECRET, Api


def test_health_endpoints_need_no_auth(api: Api) -> None:
    assert api.client.get("/healthz").json() == {"status": "ok"}
    ready = api.client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["checks"] == {"database": "ok", "storage": "ok", "redis": "ok"}


def test_service_token_is_required(api: Api) -> None:
    response = api.client.get("/api/v1/auth/me")
    assert response.status_code == 401
    wrong = api.client.get("/api/v1/auth/me", headers={"X-Service-Token": "nope"})
    assert wrong.status_code == 401
    body = wrong.json()["error"]
    assert body["code"] == "authentication_required"
    assert body["request_id"] == wrong.headers["X-Request-ID"]


def test_request_id_is_propagated_and_security_headers_set(api: Api) -> None:
    response = api.call("GET", "/auth/me", headers={"X-Request-ID": "ui-req-12345678"})
    assert response.headers["X-Request-ID"] == "ui-req-12345678"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"


def test_register_login_me_logout(api: Api) -> None:
    user = api.register("ada")
    assert user["role"] == "member"
    assert "password_hash" not in user
    token = api.login("ada")
    me = api.call("GET", "/auth/me", token)
    assert me.json()["email"] == "ada@example.test"
    assert api.call("POST", "/auth/logout", token).status_code == 204
    assert api.call("GET", "/auth/me", token).status_code == 401


def test_register_rejects_role_field_and_duplicates(api: Api) -> None:
    sneaky = api.call(
        "POST",
        "/auth/register",
        json={
            "email": "x@example.test",
            "display_name": "X",
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert sneaky.status_code == 422
    assert sneaky.json()["error"]["fields"][0]["field"] == "role"
    api.register("ada")
    duplicate = api.call(
        "POST",
        "/auth/register",
        json={"email": "ADA@example.test", "display_name": "A", "password": PASSWORD},
    )
    assert duplicate.status_code == 409


def test_login_errors_and_bad_tokens(api: Api) -> None:
    api.register("ada")
    wrong = api.call("POST", "/auth/login", json={"email": "ada@example.test", "password": "x"})
    unknown = api.call("POST", "/auth/login", json={"email": "no@example.test", "password": "x"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]
    assert api.call("GET", "/auth/me", "garbage-token").status_code == 401
    bad_scheme = api.call("GET", "/auth/me", headers={"Authorization": "Basic abc"})
    assert bad_scheme.status_code == 401


def test_login_lockout_returns_429(api: Api) -> None:
    api.register("ada")
    for _ in range(5):
        api.call("POST", "/auth/login", json={"email": "ada@example.test", "password": "nope"})
    locked = api.call(
        "POST", "/auth/login", json={"email": "ada@example.test", "password": PASSWORD}
    )
    assert locked.status_code == 429


def test_change_password_rotates_session(api: Api) -> None:
    _, token = api.user("ada")
    changed = api.call(
        "POST",
        "/auth/password/change",
        token,
        json={"current_password": PASSWORD, "new_password": "another-good-password"},
    )
    assert changed.status_code == 200
    assert api.call("GET", "/auth/me", token).status_code == 401
    assert api.call("GET", "/auth/me", changed.json()["token"]).status_code == 200
    api.login("ada", "another-good-password")


def test_forgot_and_reset_password_via_outbox(api: Api, settings: Settings) -> None:
    api.register("ada")
    for email in ("ada@example.test", "ghost@example.test"):
        response = api.call("POST", "/auth/password/forgot", json={"email": email})
        assert response.status_code == 202
    engine = create_engine(settings.database_url.get_secret_value())
    with engine.connect() as conn:
        bodies = conn.execute(select(OutboxRow.body, OutboxRow.to_email)).all()
    engine.dispose()
    assert [b.to_email for b in bodies] == ["ada@example.test"]
    link = next(line for line in bodies[0].body.splitlines() if "reset-password" in line)
    assert link.startswith("http://localhost:3000/reset-password?token=")
    token = parse_qs(urlsplit(link).query)["token"][0]
    reset = api.call(
        "POST", "/auth/password/reset", json={"token": token, "new_password": "fresh-password-99"}
    )
    assert reset.status_code == 200
    again = api.call(
        "POST", "/auth/password/reset", json={"token": token, "new_password": "fresh-password-99"}
    )
    assert again.status_code == 422
    api.login("ada", "fresh-password-99")


def test_admin_user_management(
    api: Api, monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    monkeypatch.setenv("DATABASE_URL", settings.database_url.get_secret_value())
    monkeypatch.setenv("SERVICE_AUTH_SECRET", SERVICE_SECRET)
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", "w" * 32)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://localhost:3000")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", settings.storage_local_path)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    get_settings.cache_clear()
    assert cli.main(["create-admin"]) == 2
    monkeypatch.setenv("ADMIN_EMAIL", "root@example.test")
    monkeypatch.setenv("ADMIN_PASSWORD", "short")
    assert cli.main(["create-admin"]) == 1
    monkeypatch.setenv("ADMIN_PASSWORD", "root-password-123")
    assert cli.main(["create-admin"]) == 0
    get_settings.cache_clear()

    admin_token = api.login("root", "root-password-123")
    member, member_token = api.user("mia")
    assert api.call("GET", "/admin/users", member_token).status_code == 403
    assert api.call("GET", "/admin/activity", member_token).status_code == 403
    assert api.call("GET", "/admin/activity", admin_token).status_code == 200
    listing = api.call("GET", "/admin/users", admin_token, params={"page_size": 1})
    assert listing.json()["total"] == 2
    assert len(listing.json()["items"]) == 1
    deactivated = api.call(
        "PATCH", f"/admin/users/{member['id']}", admin_token, json={"is_active": False}
    )
    assert deactivated.json()["is_active"] is False
    assert api.call("GET", "/auth/me", member_token).status_code == 401
    relogin = api.call(
        "POST", "/auth/login", json={"email": "mia@example.test", "password": PASSWORD}
    )
    assert relogin.status_code == 401
    api.call("PATCH", f"/admin/users/{member['id']}", admin_token, json={"is_active": True})
    promoted = api.call(
        "PATCH", f"/admin/users/{member['id']}", admin_token, json={"role": "admin"}
    )
    assert promoted.json()["role"] == "admin"
    me = api.call("GET", "/auth/me", admin_token).json()
    self_demote = api.call(
        "PATCH", f"/admin/users/{me['id']}", admin_token, json={"role": "member"}
    )
    assert self_demote.status_code == 422
