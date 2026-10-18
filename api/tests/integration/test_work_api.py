"""Teams, projects, tasks, comments, attachments, search, export and webhooks, end to end."""

import csv
import hashlib
import hmac
import io
import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, ClassVar

import pytest
from fastapi.testclient import TestClient

from taskboard.config import Settings
from taskboard.main import create_app
from tests.integration.conftest import Api, make_settings


def _team_with_project(api: Api) -> dict[str, Any]:
    owner, owner_token = api.user("olive")
    member, member_token = api.user("mo")
    outsider, outsider_token = api.user("xena")
    team = api.call("POST", "/teams", owner_token, json={"name": "Core"}).json()
    added = api.call(
        "POST", f"/teams/{team['id']}/members", owner_token, json={"email": "mo@example.test"}
    )
    assert added.status_code == 201
    project = api.call(
        "POST", f"/teams/{team['id']}/projects", owner_token, json={"name": "Board"}
    ).json()
    return {
        "owner": owner,
        "owner_token": owner_token,
        "member": member,
        "member_token": member_token,
        "outsider": outsider,
        "outsider_token": outsider_token,
        "team": team,
        "project": project,
    }


def _task(api: Api, token: str, project_id: str, **fields: Any) -> dict[str, Any]:
    response = api.call(
        "POST", f"/projects/{project_id}/tasks", token, json={"title": "T", **fields}
    )
    assert response.status_code == 201, response.text
    task: dict[str, Any] = response.json()
    return task


def test_team_and_project_flow(api: Api) -> None:
    w = _team_with_project(api)
    team_id, project_id = w["team"]["id"], w["project"]["id"]
    detail = api.call("GET", f"/teams/{team_id}", w["member_token"]).json()
    assert {m["display_name"] for m in detail["members"]} == {"Olive", "Mo"}
    assert [t["name"] for t in api.call("GET", "/teams", w["member_token"]).json()] == ["Core"]
    assert len(api.call("GET", "/projects", w["member_token"]).json()) == 1
    assert len(api.call("GET", f"/teams/{team_id}/projects", w["member_token"]).json()) == 1
    forbidden = api.call(
        "POST", f"/teams/{team_id}/projects", w["member_token"], json={"name": "X"}
    )
    assert forbidden.status_code == 403
    renamed = api.call(
        "PATCH", f"/projects/{project_id}", w["owner_token"], json={"name": "Renamed"}
    )
    assert renamed.json()["name"] == "Renamed"
    archived = api.call("POST", f"/projects/{project_id}/archive", w["owner_token"])
    assert archived.json()["is_archived"] is True
    blocked = api.call(
        "POST", f"/projects/{project_id}/tasks", w["member_token"], json={"title": "x"}
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "project_archived"
    removed = api.call("DELETE", f"/teams/{team_id}/members/{w['member']['id']}", w["owner_token"])
    assert removed.status_code == 204
    assert api.call("GET", f"/teams/{team_id}", w["member_token"]).status_code == 404


def test_cross_team_access_is_not_found(api: Api) -> None:
    w = _team_with_project(api)
    task = _task(api, w["member_token"], w["project"]["id"])
    comment = api.call(
        "POST", f"/tasks/{task['id']}/comments", w["member_token"], json={"body": "hi"}
    ).json()
    upload = api.call(
        "POST",
        f"/tasks/{task['id']}/attachments",
        w["member_token"],
        files={"file": ("a.txt", b"secret", "text/plain")},
    ).json()
    t = w["outsider_token"]
    probes = [
        ("GET", f"/teams/{w['team']['id']}"),
        ("GET", f"/teams/{w['team']['id']}/projects"),
        ("GET", f"/projects/{w['project']['id']}"),
        ("GET", f"/projects/{w['project']['id']}/tasks"),
        ("GET", f"/projects/{w['project']['id']}/export.csv"),
        ("GET", f"/projects/{w['project']['id']}/activity"),
        ("GET", f"/tasks/{task['id']}"),
        ("GET", f"/tasks/{task['id']}/comments"),
        ("GET", f"/tasks/{task['id']}/attachments"),
        ("GET", f"/attachments/{upload['id']}/download"),
        ("DELETE", f"/tasks/{task['id']}"),
        ("DELETE", f"/comments/{comment['id']}"),
    ]
    for method, path in probes:
        assert api.call(method, path, t).status_code == 404, path
    patch = api.call("PATCH", f"/tasks/{task['id']}", t, json={"title": "pwned"})
    assert patch.status_code == 404
    search = api.call("GET", "/search/tasks", t).json()
    assert search["total"] == 0


def test_task_crud_and_validation(api: Api) -> None:
    w = _team_with_project(api)
    pid = w["project"]["id"]
    task = _task(
        api,
        w["member_token"],
        pid,
        description="**bold**",
        assignee_id=w["member"]["id"],
        due_date="2026-12-01",
        labels=["ui", "ui", "api"],
    )
    assert task["labels"] == ["ui", "api"]
    bad_assignee = api.call(
        "POST",
        f"/projects/{pid}/tasks",
        w["member_token"],
        json={"title": "x", "assignee_id": w["outsider"]["id"]},
    )
    assert bad_assignee.status_code == 422
    updated = api.call(
        "PATCH",
        f"/tasks/{task['id']}",
        w["member_token"],
        json={"assignee_id": None, "priority": "high"},
    ).json()
    assert updated["assignee_id"] is None
    assert updated["priority"] == "high"
    null_title = api.call("PATCH", f"/tasks/{task['id']}", w["member_token"], json={"title": None})
    assert null_title.status_code == 422
    assert api.call("GET", f"/tasks/{task['id']}", w["owner_token"]).json()["priority"] == "high"
    assert api.call("DELETE", f"/tasks/{task['id']}", w["member_token"]).status_code == 204
    assert api.call("GET", f"/tasks/{task['id']}", w["member_token"]).status_code == 404


def test_comments_only_editable_by_author(api: Api) -> None:
    w = _team_with_project(api)
    task = _task(api, w["member_token"], w["project"]["id"])
    comment = api.call(
        "POST", f"/tasks/{task['id']}/comments", w["member_token"], json={"body": "first"}
    ).json()
    assert comment["author_name"] == "Mo"
    other = api.call("PATCH", f"/comments/{comment['id']}", w["owner_token"], json={"body": "x"})
    assert other.status_code == 403
    edited = api.call(
        "PATCH", f"/comments/{comment['id']}", w["member_token"], json={"body": "edited"}
    )
    assert edited.json()["body"] == "edited"
    listing = api.call("GET", f"/tasks/{task['id']}/comments", w["owner_token"]).json()
    assert [c["body"] for c in listing] == ["edited"]
    assert api.call("DELETE", f"/comments/{comment['id']}", w["member_token"]).status_code == 204


def test_attachments_upload_download_and_limits(api: Api) -> None:
    w = _team_with_project(api)
    task = _task(api, w["member_token"], w["project"]["id"])
    content = b"<html><script>alert(1)</script></html>"
    up = api.call(
        "POST",
        f"/tasks/{task['id']}/attachments",
        w["member_token"],
        files={"file": ("../../rapport été;x.html", content, "text/html")},
    )
    assert up.status_code == 201
    attachment = up.json()
    assert attachment["filename"] == "rapport été;x.html"
    down = api.call("GET", f"/attachments/{attachment['id']}/download", w["owner_token"])
    assert down.content == content
    assert down.headers["content-type"] == "application/octet-stream"
    assert down.headers["x-content-type-options"] == "nosniff"
    assert down.headers["content-security-policy"].startswith("sandbox")
    disposition = down.headers["content-disposition"]
    assert disposition.startswith('attachment; filename="rapport _t__x.html"')
    assert "filename*=UTF-8''rapport%20%C3%A9t%C3%A9%3Bx.html" in disposition
    too_big = api.call(
        "POST",
        f"/tasks/{task['id']}/attachments",
        w["member_token"],
        files={"file": ("big.bin", b"x" * 5000, "application/octet-stream")},
    )
    assert too_big.status_code == 413
    huge = api.call(
        "POST",
        f"/tasks/{task['id']}/attachments",
        w["member_token"],
        files={"file": ("huge.bin", b"x" * 80_000, "application/octet-stream")},
    )
    assert huge.status_code == 413
    assert len(api.call("GET", f"/tasks/{task['id']}/attachments", w["owner_token"]).json()) == 1


def test_search_filters_sorting_and_pagination(api: Api) -> None:
    w = _team_with_project(api)
    pid, token = w["project"]["id"], w["member_token"]
    _task(api, token, pid, title="Bravo 100%", priority="low", labels=["x"], due_date="2026-11-01")
    _task(api, token, pid, title="alpha", priority="high", assignee_id=w["member"]["id"])
    _task(
        api, token, pid, title="Charlie", priority="medium", status="done", description="has_under"
    )
    sort = api.call("GET", "/search/tasks", token, params={"sort": "title", "order": "asc"}).json()
    assert [t["title"] for t in sort["items"]] == ["alpha", "Bravo 100%", "Charlie"]
    prio = api.call(
        "GET", "/search/tasks", token, params={"sort": "priority", "order": "desc"}
    ).json()
    assert [t["priority"] for t in prio["items"]] == ["high", "medium", "low"]
    for field in ("status", "due_date", "created_at", "updated_at", "assignee"):
        assert api.call("GET", "/search/tasks", token, params={"sort": field}).status_code == 200
    assert api.call("GET", "/search/tasks", token, params={"q": "100%"}).json()["total"] == 1
    assert api.call("GET", "/search/tasks", token, params={"q": "%"}).json()["total"] == 1
    assert api.call("GET", "/search/tasks", token, params={"q": "has_"}).json()["total"] == 1
    assert api.call("GET", "/search/tasks", token, params={"status": "done"}).json()["total"] == 1
    assert api.call("GET", "/search/tasks", token, params={"label": "x"}).json()["total"] == 1
    mine = api.call("GET", "/search/tasks", token, params={"assignee_id": w["member"]["id"]}).json()
    assert [t["title"] for t in mine["items"]] == ["alpha"]
    due = api.call("GET", "/search/tasks", token, params={"due_before": "2026-12-01"}).json()
    assert due["total"] == 1
    page = api.call("GET", "/search/tasks", token, params={"page": 2, "page_size": 2}).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1
    injected = api.call("GET", "/search/tasks", token, params={"sort": "title; DROP TABLE tasks"})
    assert injected.status_code == 422
    assert api.call("GET", "/search/tasks", token, params={"order": "sideways"}).status_code == 422
    listed = api.call("GET", f"/projects/{pid}/tasks", token, params={"status": "todo"}).json()
    assert listed["total"] == 2


def test_csv_export(api: Api) -> None:
    w = _team_with_project(api)
    _task(api, w["member_token"], w["project"]["id"], title="=cmd|' /C calc'!A0")
    response = api.call("GET", f"/projects/{w['project']['id']}/export.csv", w["member_token"])
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[1][1].startswith("'=")


def test_activity_feed(api: Api) -> None:
    w = _team_with_project(api)
    task = _task(api, w["member_token"], w["project"]["id"])
    api.call("PATCH", f"/tasks/{task['id']}", w["member_token"], json={"status": "in_progress"})
    api.call("POST", f"/tasks/{task['id']}/comments", w["member_token"], json={"body": "c"})
    feed = api.call("GET", f"/projects/{w['project']['id']}/activity", w["owner_token"]).json()
    kinds = [e["event_type"] for e in feed["items"]]
    assert set(kinds) == {"member_added", "task_created", "status_changed", "comment_added"}


class _Receiver(BaseHTTPRequestHandler):
    received: ClassVar[list[dict[str, Any]]] = []
    event: ClassVar[threading.Event] = threading.Event()

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        _Receiver.received.append(
            {"body": json.loads(self.rfile.read(length)), "headers": dict(self.headers)}
        )
        self.send_response(204)
        self.end_headers()
        _Receiver.event.set()

    def log_message(self, format: str, *args: Any) -> None:
        return None


@pytest.fixture
def receiver() -> Iterator[str]:
    server = HTTPServer(("127.0.0.1", 0), _Receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _Receiver.received.clear()
    _Receiver.event.clear()
    yield f"http://127.0.0.1:{server.server_address[1]}/hook"
    server.shutdown()


def test_webhook_fires_on_status_change(settings: Settings, tmp_path: Path, receiver: str) -> None:
    permissive = make_settings(
        tmp_path / "files", webhook_allow_http=True, webhook_allow_private_targets=True
    )
    with TestClient(create_app(permissive)) as client:
        api = Api(client)
        w = _team_with_project(api)
        pid = w["project"]["id"]
        hooked = api.call(
            "PATCH", f"/projects/{pid}", w["owner_token"], json={"webhook_url": receiver}
        )
        assert hooked.json()["webhook_url"] == receiver
        assert api.call("GET", f"/projects/{pid}", w["member_token"]).json()["webhook_url"] is None
        task = _task(api, w["member_token"], pid)
        api.call("PATCH", f"/tasks/{task['id']}", w["member_token"], json={"status": "done"})
        assert _Receiver.event.wait(5)
    payload = _Receiver.received[0]["body"]
    assert payload["event"] == "task.status_changed"
    assert payload["task_id"] == task["id"]
    assert payload["old_status"] == "todo"
    assert payload["new_status"] == "done"
    assert payload["actor_id"] == w["member"]["id"]
    key = hooked.json()["webhook_signing_key"]
    raw = json.dumps(payload, separators=(",", ":")).encode()
    expected = "sha256=" + hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()
    assert _Receiver.received[0]["headers"]["X-Taskboard-Signature"] == expected


def test_webhook_url_must_be_public_https(api: Api) -> None:
    w = _team_with_project(api)
    for url in ("http://example.test/x", "https://169.254.169.254/", "https://localhost/"):
        response = api.call(
            "PATCH", f"/projects/{w['project']['id']}", w["owner_token"], json={"webhook_url": url}
        )
        assert response.status_code == 422, url


def test_json_routes_reject_large_bodies(api: Api) -> None:
    w = _team_with_project(api)
    big = {"title": "x", "description": "y" * 300_000}
    response = api.call(
        "POST", f"/projects/{w['project']['id']}/tasks", w["member_token"], json=big
    )
    assert response.status_code == 413
