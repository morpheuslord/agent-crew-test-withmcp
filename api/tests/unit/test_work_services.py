"""Teams, projects, tasks, comments, attachments and activity against fakes."""

import csv
import io
from datetime import date
from uuid import UUID

import pytest

from taskboard.domain.entities import TaskChanges, TaskDraft, TaskFilter, User
from taskboard.domain.enums import ActivityType, Role, TaskStatus
from taskboard.domain.errors import (
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    ProjectArchivedError,
    ValidationFailedError,
)
from taskboard.services.attachments import clean_content_type, clean_filename
from taskboard.services.export import neutralise_cell
from tests.unit.conftest import World


def _setup(world: World) -> tuple[User, User, User, UUID, UUID]:
    owner = world.user("olive")
    member = world.user("mo")
    outsider = world.user("xena")
    team = world.teams.create_team(owner, " Core ")
    world.teams.add_member(owner, team.id, "MO@example.test")
    project = world.projects.create(owner, team.id, "Board", "https://hooks.example.test/x")
    return owner, member, outsider, team.id, project.id


def test_team_membership_rules(world: World) -> None:
    owner, member, outsider, team_id, _ = _setup(world)
    assert [t.name for t in world.teams.list_my_teams(member)] == ["Core"]
    with pytest.raises(NotFoundError):
        world.teams.get_team(outsider, team_id)
    with pytest.raises(PermissionDeniedError):
        world.teams.add_member(member, team_id, outsider.email)
    with pytest.raises(ConflictError):
        world.teams.add_member(owner, team_id, member.email)
    with pytest.raises(NotFoundError):
        world.teams.add_member(owner, team_id, "nobody@example.test")
    with pytest.raises(ValidationFailedError):
        world.teams.remove_member(owner, team_id, owner.id)
    world.teams.remove_member(owner, team_id, member.id)
    with pytest.raises(NotFoundError):
        world.teams.remove_member(owner, team_id, member.id)
    with pytest.raises(NotFoundError):
        world.teams.get_team(member, team_id)
    kinds = [e.event_type for e in world.store.activity]
    assert kinds == [ActivityType.MEMBER_ADDED, ActivityType.MEMBER_REMOVED]


def test_admin_sees_every_team(world: World) -> None:
    _, _, _, team_id, _ = _setup(world)
    admin = world.user("root", Role.ADMIN)
    assert world.teams.get_team(admin, team_id).team.id == team_id


def test_webhook_url_hidden_from_non_owners(world: World) -> None:
    owner, member, _, team_id, project_id = _setup(world)
    assert world.projects.get(owner, project_id).webhook_url is not None
    assert world.projects.get(member, project_id).webhook_url is None
    assert all(p.webhook_url is None for p in world.projects.list_my_projects(member))
    assert all(p.webhook_url is None for p in world.projects.list_team_projects(member, team_id))
    assert all(p.webhook_url is None for p in world.teams.get_team(member, team_id).projects)


def test_project_management_rules(world: World) -> None:
    owner, member, outsider, team_id, project_id = _setup(world)
    with pytest.raises(PermissionDeniedError):
        world.projects.create(member, team_id, "Nope", None)
    with pytest.raises(NotFoundError):
        world.projects.get(outsider, project_id)
    with pytest.raises(ValidationFailedError):
        world.projects.create(owner, team_id, "Bad hook", "http://169.254.169.254/latest")
    renamed = world.projects.update(
        owner, project_id, name="Renamed", webhook_url=None, clear_webhook=True
    )
    assert renamed.name == "Renamed"
    assert renamed.webhook_url is None
    archived = world.projects.archive(owner, project_id)
    assert archived.is_archived
    with pytest.raises(ProjectArchivedError):
        world.projects.update(owner, project_id, name="x", webhook_url=None, clear_webhook=False)
    with pytest.raises(ProjectArchivedError):
        world.tasks.create(member, project_id, TaskDraft(title="Late"))


def test_task_lifecycle_and_webhook(world: World) -> None:
    _, member, outsider, _, project_id = _setup(world)
    task = world.tasks.create(
        member,
        project_id,
        TaskDraft(title=" Write docs ", assignee_id=member.id, labels=("docs",)),
    )
    assert task.title == "Write docs"
    with pytest.raises(NotFoundError):
        world.tasks.get(outsider, task.id)
    with pytest.raises(ValidationFailedError):
        world.tasks.create(member, project_id, TaskDraft(title="x", assignee_id=outsider.id))
    updated = world.tasks.update(
        member, task.id, TaskChanges(status=TaskStatus.DONE, title="Docs", clear=frozenset())
    )
    assert updated.status is TaskStatus.DONE
    assert len(world.notifier.sent) == 1
    url, event = world.notifier.sent[0]
    assert url == "https://hooks.example.test/x"
    assert event.to_payload()["old_status"] == "todo"
    assert event.to_payload()["new_status"] == "done"
    kinds = [e.event_type for e in world.store.activity]
    assert ActivityType.TASK_UPDATED in kinds
    assert ActivityType.STATUS_CHANGED in kinds
    cleared = world.tasks.update(
        member, task.id, TaskChanges(clear=frozenset({"assignee_id", "due_date"}))
    )
    assert cleared.assignee_id is None
    same = world.tasks.update(member, task.id, TaskChanges(status=TaskStatus.DONE))
    assert same.status is TaskStatus.DONE
    assert len(world.notifier.sent) == 1


def test_task_search_is_scoped_to_visible_teams(world: World) -> None:
    owner, member, outsider, _, project_id = _setup(world)
    world.tasks.create(member, project_id, TaskDraft(title="Alpha"))
    other_team = world.teams.create_team(outsider, "Other")
    other_project = world.projects.create(outsider, other_team.id, "Secret", None)
    world.tasks.create(outsider, other_project.id, TaskDraft(title="Alpha secret"))
    assert world.tasks.search(member, TaskFilter(text="alpha")).total == 1
    assert world.tasks.search(world.user("root", Role.ADMIN), TaskFilter(text="alpha")).total == 2
    assert world.tasks.list_project_tasks(owner, project_id, TaskFilter()).total == 1


def test_task_delete_removes_blobs(world: World) -> None:
    _, member, _, _, project_id = _setup(world)
    task = world.tasks.create(member, project_id, TaskDraft(title="With file"))
    world.attachments.upload(
        member, task.id, filename="a.txt", content_type="text/plain", data=io.BytesIO(b"hello")
    )
    assert len(world.storage.blobs) == 1
    world.tasks.delete(member, task.id)
    assert world.storage.blobs == {}


def test_comment_rules(world: World) -> None:
    owner, member, outsider, _, project_id = _setup(world)
    task = world.tasks.create(member, project_id, TaskDraft(title="Discuss"))
    comment = world.comments.add(member, task.id, "First!")
    assert [c.body for c in world.comments.list(owner, task.id)] == ["First!"]
    with pytest.raises(PermissionDeniedError):
        world.comments.edit(owner, comment.id, "Hijack")
    with pytest.raises(NotFoundError):
        world.comments.delete(outsider, comment.id)
    assert world.comments.edit(member, comment.id, "Edited").body == "Edited"
    world.comments.delete(member, comment.id)
    assert world.comments.list(owner, task.id) == []
    with pytest.raises(NotFoundError):
        world.comments.edit(member, comment.id, "gone")


def test_attachment_upload_limits_and_access(world: World) -> None:
    _, member, outsider, _, project_id = _setup(world)
    task = world.tasks.create(member, project_id, TaskDraft(title="Files"))
    attachment = world.attachments.upload(
        member,
        task.id,
        filename="../../etc/passwd",
        content_type="text/html; charset=utf-8",
        data=io.BytesIO(b"data"),
    )
    assert attachment.filename == "passwd"
    assert attachment.storage_key.startswith("attachments/")
    with pytest.raises(PayloadTooLargeError):
        world.attachments.upload(
            member, task.id, filename="big.bin", content_type=None, data=io.BytesIO(b"x" * 2048)
        )
    with pytest.raises(NotFoundError):
        world.attachments.open(outsider, attachment.id)
    found, stream = world.attachments.open(member, attachment.id)
    assert b"".join(stream) == b"data"
    assert [a.id for a in world.attachments.list(member, task.id)] == [found.id]
    world.storage.blobs.clear()
    with pytest.raises(NotFoundError):
        world.attachments.open(member, attachment.id)


def test_filename_and_content_type_cleaning() -> None:
    assert clean_filename("C:\\Users\\me\\report.pdf") == "report.pdf"
    assert clean_filename('evil"\r\nname.txt') == 'evil"name.txt'
    assert clean_filename("") == "attachment"
    assert clean_filename("...") == "attachment"
    long_name = "a" * 300 + ".txt"
    assert len(clean_filename(long_name)) == 200
    assert clean_filename(long_name).endswith(".txt")
    assert clean_content_type("Image/PNG; foo=bar") == "image/png"
    assert clean_content_type(None) == "application/octet-stream"
    assert clean_content_type("nonsense") == "application/octet-stream"


def test_activity_feeds(world: World) -> None:
    owner, member, outsider, _, project_id = _setup(world)
    world.tasks.create(member, project_id, TaskDraft(title="Tracked"))
    feed = world.activity.project_feed(member, project_id, 1, 50)
    assert {e.event_type for e in feed.items} == {
        ActivityType.MEMBER_ADDED,
        ActivityType.TASK_CREATED,
    }
    with pytest.raises(NotFoundError):
        world.activity.project_feed(outsider, project_id, 1, 50)
    with pytest.raises(PermissionDeniedError):
        world.activity.global_feed(owner, 1, 50)
    assert world.activity.global_feed(world.user("root", Role.ADMIN), 1, 50).total == 2


def test_csv_export_neutralises_formulas(world: World) -> None:
    _, member, outsider, _, project_id = _setup(world)
    world.tasks.create(
        member,
        project_id,
        TaskDraft(
            title='=HYPERLINK("http://evil")',
            assignee_id=member.id,
            due_date=date(2026, 11, 1),
            labels=("a", "b"),
        ),
    )
    _, content = world.exporter.export(member, project_id)
    rows = list(csv.reader(io.StringIO(content)))
    assert rows[0][0] == "id"
    assert rows[1][1].startswith("'=")
    assert rows[1][4] == "Mo"
    assert rows[1][6] == "a;b"
    with pytest.raises(NotFoundError):
        world.exporter.export(outsider, project_id)
    assert neutralise_cell("+1") == "'+1"
    assert neutralise_cell("plain") == "plain"
