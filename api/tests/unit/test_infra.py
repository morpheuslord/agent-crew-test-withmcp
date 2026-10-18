"""Rate limiting, storage, mailer, logging, password hashing and settings."""

import io
import json
import logging
import sys
from pathlib import Path
from typing import Any

import boto3
import pytest
import redis
from moto import mock_aws
from pydantic import ValidationError

from taskboard.api.routers.tasks import content_disposition
from taskboard.config import Settings
from taskboard.domain.errors import ValidationFailedError
from taskboard.infra.mailer import LogOutboxMailer
from taskboard.infra.rate_limit import InMemoryRateLimiter, RedisRateLimiter, limiter_key
from taskboard.infra.storage.base import BlobNotFoundError, check_key
from taskboard.infra.storage.local import LocalFileStorage
from taskboard.infra.storage.s3 import S3Storage
from taskboard.logging_setup import JsonFormatter, accept_request_id, request_id_var
from taskboard.services.security import Argon2PasswordHasher, hash_token, new_token
from tests.fakes import FakeOutbox, Store

KEY = "attachments/" + "a" * 32


def test_in_memory_limiter_counts_and_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = InMemoryRateLimiter()
    now = [100.0]
    monkeypatch.setattr("taskboard.infra.rate_limit.time.monotonic", lambda: now[0])
    assert limiter.hit("k", 10) == 1
    assert limiter.hit("k", 10) == 2
    assert limiter.count("k") == 2
    now[0] = 111.0
    assert limiter.count("k") == 0
    assert limiter.hit("k", 10) == 1
    limiter.reset("k")
    assert limiter.count("k") == 0


def test_limiter_key_hides_identifiers() -> None:
    key = limiter_key("login-fail", "Ada@Example.test")
    assert "ada" not in key.lower()
    assert key == limiter_key("login-fail", "ada@example.test")


def test_redis_limiter_falls_back_when_redis_is_down() -> None:
    broken = redis.Redis(host="127.0.0.1", port=1, socket_connect_timeout=0.05)
    limiter = RedisRateLimiter(broken, InMemoryRateLimiter())
    assert limiter.hit("k", 60) == 1
    assert limiter.count("k") == 1
    limiter.reset("k")
    assert limiter.count("k") == 0


def test_storage_keys_are_validated() -> None:
    assert check_key(KEY) == KEY
    for bad in ["../etc/passwd", "attachments/../../x", "attachments/ABC", ""]:
        with pytest.raises(ValueError, match="invalid storage key"):
            check_key(bad)


def test_local_storage_round_trip(tmp_path: Path) -> None:
    storage = LocalFileStorage(str(tmp_path / "files"))
    storage.check()
    storage.save(KEY, io.BytesIO(b"hello world"), 11)
    assert b"".join(storage.open(KEY)) == b"hello world"
    assert not list((tmp_path / "files" / "attachments").glob(".upload-*"))
    storage.delete(KEY)
    storage.delete(KEY)
    with pytest.raises(BlobNotFoundError):
        storage.open(KEY)


def test_local_storage_cleans_up_failed_writes(tmp_path: Path) -> None:
    class Exploding(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            raise OSError("disk on fire")

    storage = LocalFileStorage(str(tmp_path))
    with pytest.raises(OSError, match="disk on fire"):
        storage.save(KEY, Exploding(), 10)
    assert not any((tmp_path / "attachments").iterdir())


def test_s3_storage_round_trip() -> None:
    with mock_aws():
        client = boto3.client("s3", region_name="eu-west-1")
        client.create_bucket(
            Bucket="tb-test", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"}
        )
        storage = S3Storage(client, "tb-test")
        storage.check()
        storage.save(KEY, io.BytesIO(b"bytes"), 5)
        assert b"".join(storage.open(KEY)) == b"bytes"
        head = client.head_object(Bucket="tb-test", Key=KEY)
        assert head["ServerSideEncryption"] == "aws:kms"
        storage.delete(KEY)
        with pytest.raises(BlobNotFoundError):
            storage.open(KEY)


def test_mailer_writes_outbox_and_log(caplog: pytest.LogCaptureFixture) -> None:
    store = Store()
    mailer = LogOutboxMailer(FakeOutbox(store))
    with caplog.at_level(logging.INFO, logger="taskboard.mail"):
        mailer.send("a@example.test", "Hello", "Body text")
    assert store.outbox[0].subject == "Hello"
    assert any(getattr(r, "body", None) == "Body text" for r in caplog.records)
    with pytest.raises(ValidationFailedError):
        mailer.send("a@example.test\r\nBcc: x@evil.test", "Hi", "x")
    with pytest.raises(ValidationFailedError):
        mailer.send("a@example.test", "Hi\nBcc: x@evil.test", "x")


def test_json_formatter_includes_request_id_and_extras() -> None:
    token = request_id_var.set("req-12345678")
    try:
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "hello %s", ("you",), None)
        record.custom = "value"
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            record.exc_info = sys.exc_info()
        payload: dict[str, Any] = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert payload["msg"] == "hello you"
    assert payload["request_id"] == "req-12345678"
    assert payload["custom"] == "value"
    assert "RuntimeError" in payload["exc"]


def test_request_ids_are_validated() -> None:
    assert accept_request_id("abcdef12-3456") == "abcdef12-3456"
    generated = accept_request_id("bad id\nwith newline")
    assert generated != "bad id\nwith newline"
    assert len(generated) == 36
    assert accept_request_id(None) != accept_request_id(None)


def test_argon2_hasher() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("correct-horse-battery")
    assert hashed.startswith("$argon2id$")
    assert hasher.verify(hashed, "correct-horse-battery")
    assert not hasher.verify(hashed, "wrong")
    assert not hasher.verify("not-a-hash", "wrong")
    hasher.burn("anything")


def test_tokens_are_random_and_hashed() -> None:
    a, b = new_token(), new_token()
    assert a != b
    assert len(a) >= 43
    assert hash_token(a) != a
    assert len(hash_token(a)) == 64


BASE_ENV = {
    "DATABASE_URL": "postgresql+psycopg://u:p@db/tb",
    "SERVICE_AUTH_SECRET": "x" * 32,
    "WEBHOOK_SIGNING_SECRET": "y" * 32,
    "PUBLIC_BASE_URL": "https://taskboard.example.test",
}


OPTIONAL_KEYS = (
    "ENVIRONMENT",
    "MIGRATION_DATABASE_URL",
    "STORAGE_BACKEND",
    "WEBHOOK_ALLOW_HTTP",
    "WEBHOOK_ALLOW_PRIVATE_TARGETS",
)


def _settings(monkeypatch: pytest.MonkeyPatch, **extra: str) -> Settings:
    for key in OPTIONAL_KEYS:
        monkeypatch.delenv(key, raising=False)
    for key, value in {**BASE_ENV, **extra}.items():
        monkeypatch.setenv(key, value)
    return Settings()


def test_settings_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(monkeypatch)
    assert settings.migrations_url.endswith("/tb")
    with pytest.raises(ValidationError):
        _settings(monkeypatch, SERVICE_AUTH_SECRET="short")
    with pytest.raises(ValidationError):
        _settings(monkeypatch, STORAGE_BACKEND="s3")
    with pytest.raises(ValidationError):
        _settings(monkeypatch, WEBHOOK_ALLOW_HTTP="true")
    with pytest.raises(ValidationError):
        _settings(monkeypatch, PUBLIC_BASE_URL="http://insecure.example.test")
    dev = _settings(
        monkeypatch,
        ENVIRONMENT="development",
        WEBHOOK_ALLOW_HTTP="true",
        PUBLIC_BASE_URL="http://localhost:3000",
        WEBHOOK_ALLOW_PRIVATE_TARGETS="false",
    )
    assert dev.webhook_allow_http


def test_content_disposition_is_header_safe() -> None:
    header = content_disposition('a"b\\c;d\r\ne.txt')
    assert "\r" not in header
    assert "\n" not in header
    assert header.startswith('attachment; filename="a_b_c_d__e.txt"')
    assert "filename*=UTF-8''a%22b%5Cc%3Bd%0D%0Ae.txt" in header
