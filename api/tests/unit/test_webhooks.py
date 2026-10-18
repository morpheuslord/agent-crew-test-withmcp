"""SSRF guard and webhook delivery."""

import hashlib
import hmac
import json
import threading
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest

from taskboard.domain.entities import StatusChangedEvent
from taskboard.domain.enums import TaskStatus
from taskboard.domain.errors import ValidationFailedError
from taskboard.infra.webhooks.notifier import (
    HttpWebhookNotifier,
    NullWebhookNotifier,
    project_signing_key,
)
from taskboard.infra.webhooks.url_policy import ResolvedTarget, WebhookUrlPolicy, system_resolver

SECRET = b"s" * 32


def resolver_for(*addresses: str) -> Callable[[str, int], list[str]]:
    def _resolve(host: str, port: int) -> list[str]:
        return list(addresses)

    return _resolve


def _strict(*addresses: str) -> WebhookUrlPolicy:
    return WebhookUrlPolicy(
        allow_http=False, allow_private=False, resolver=resolver_for(*addresses)
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://hooks.example.test/x",
        "ftp://hooks.example.test/x",
        "https://user:pw@hooks.example.test/x",
        "https:///nohost",
        "https://169.254.169.254/latest/meta-data/",
        "https://127.0.0.1/",
        "https://[::1]/",
        "https://10.1.2.3/",
        "https://localhost/hook",
        "https://hooks.example.test:99999/",
        "https://" + "a" * 2050 + ".test/",
    ],
)
def test_validate_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(ValidationFailedError):
        _strict("93.184.215.14").validate(url)


def test_validate_accepts_public_https() -> None:
    assert _strict().validate(" https://hooks.example.test/x?y=1 ") == (
        "https://hooks.example.test/x?y=1"
    )


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.5",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "::1",
        "fd00::1",
        "::ffff:10.0.0.1",
        "224.0.0.1",
        "0.0.0.1",
    ],
)
def test_resolve_rejects_hosts_resolving_to_private_addresses(address: str) -> None:
    with pytest.raises(ValidationFailedError):
        _strict(address).resolve("https://rebind.example.test/hook")


def test_resolve_rejects_mixed_answers_and_failures() -> None:
    with pytest.raises(ValidationFailedError):
        _strict("93.184.215.14", "10.0.0.1").resolve("https://mixed.example.test/")
    with pytest.raises(ValidationFailedError):
        _strict().resolve("https://empty.example.test/")

    def broken(host: str, port: int) -> list[str]:
        raise OSError("nxdomain")

    policy = WebhookUrlPolicy(allow_http=False, allow_private=False, resolver=broken)
    with pytest.raises(ValidationFailedError):
        policy.resolve("https://nx.example.test/")


def test_resolve_pins_the_validated_address() -> None:
    target = _strict("93.184.215.14").resolve("https://hooks.example.test:8443/p?q=1")
    assert target.connect_url == "https://93.184.215.14:8443/p?q=1"
    assert target.host_header == "hooks.example.test:8443"
    v6 = ResolvedTarget("https", "h.example.test", 443, "2606:2800:220:1::1", "/")
    assert v6.connect_url == "https://[2606:2800:220:1::1]:443/"
    assert v6.host_header == "h.example.test"


def test_permissive_policy_for_local_development() -> None:
    policy = WebhookUrlPolicy(
        allow_http=True, allow_private=True, resolver=resolver_for("127.0.0.1")
    )
    assert policy.validate("http://localhost:9000/hook") == "http://localhost:9000/hook"
    assert policy.resolve("http://localhost:9000/hook").address == "127.0.0.1"


def test_system_resolver_resolves_literals() -> None:
    assert "127.0.0.1" in system_resolver("127.0.0.1", 80)


def _event() -> StatusChangedEvent:
    return StatusChangedEvent(
        task_id=uuid4(),
        project_id=uuid4(),
        old_status=TaskStatus.TODO,
        new_status=TaskStatus.DONE,
        actor_id=uuid4(),
        timestamp=datetime(2026, 10, 18, tzinfo=UTC),
    )


def _notifier(
    handler: Callable[[httpx.Request], httpx.Response],
    executor: ThreadPoolExecutor,
    *addresses: str,
) -> HttpWebhookNotifier:
    def factory() -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)

    return HttpWebhookNotifier(
        policy=_strict(*(addresses or ("93.184.215.14",))),
        signing_secret=SECRET,
        timeout_seconds=1.0,
        max_attempts=3,
        client_factory=factory,
        executor=executor,
        backoff_seconds=0.0,
    )


def test_delivery_posts_signed_payload_to_pinned_address() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(204)

    executor = ThreadPoolExecutor(max_workers=1)
    event = _event()
    _notifier(handler, executor).notify("https://hooks.example.test/in", event)
    executor.shutdown(wait=True)
    assert len(seen) == 1
    request = seen[0]
    assert str(request.url) == "https://93.184.215.14/in"
    assert request.headers["host"] == "hooks.example.test"
    assert request.extensions["sni_hostname"] == "hooks.example.test"
    body = request.content
    assert json.loads(body) == event.to_payload()
    key = project_signing_key(SECRET, event.project_id)
    expected = "sha256=" + hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
    assert request.headers["x-taskboard-signature"] == expected
    other_key = project_signing_key(SECRET, uuid4())
    assert other_key != key


def test_delivery_retries_then_gives_up_without_following_redirects() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ConnectError("refused", request=request)
        return httpx.Response(302, headers={"Location": "http://169.254.169.254/"})

    executor = ThreadPoolExecutor(max_workers=1)
    _notifier(handler, executor).notify("https://hooks.example.test/in", _event())
    executor.shutdown(wait=True)
    assert len(calls) == 3


def test_delivery_stops_when_target_becomes_private() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200)

    executor = ThreadPoolExecutor(max_workers=1)
    _notifier(handler, executor, "10.0.0.7").notify("https://hooks.example.test/in", _event())
    executor.shutdown(wait=True)
    assert calls == []


def test_large_responses_are_not_read_fully() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x" * (200 * 1024))

    executor = ThreadPoolExecutor(max_workers=1)
    _notifier(handler, executor).notify("https://hooks.example.test/in", _event())
    executor.shutdown(wait=True)


def test_null_notifier_and_default_client() -> None:
    NullWebhookNotifier().notify("https://x.example.test", _event())
    notifier = HttpWebhookNotifier(
        policy=_strict(), signing_secret=SECRET, timeout_seconds=1.0, max_attempts=1
    )
    with notifier._default_client() as client:
        assert client.follow_redirects is False
    notifier.shutdown()


def test_backlog_is_bounded() -> None:
    gate = threading.Event()
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        gate.wait(5)
        return httpx.Response(204)

    executor = ThreadPoolExecutor(max_workers=1)
    notifier = HttpWebhookNotifier(
        policy=_strict("93.184.215.14"),
        signing_secret=SECRET,
        timeout_seconds=1.0,
        max_attempts=1,
        client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
        executor=executor,
        max_pending=1,
    )
    notifier.notify("https://hooks.example.test/in", _event())
    notifier.notify("https://hooks.example.test/in", _event())
    gate.set()
    executor.shutdown(wait=True)
    assert len(calls) == 1


class _SlowStream(httpx.SyncByteStream):
    def __iter__(self) -> Iterator[bytes]:
        for _ in range(5):
            time.sleep(0.05)
            yield b"x"


def test_slow_drip_responses_hit_the_attempt_deadline() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, stream=_SlowStream())

    executor = ThreadPoolExecutor(max_workers=1)
    notifier = HttpWebhookNotifier(
        policy=_strict("93.184.215.14"),
        signing_secret=SECRET,
        timeout_seconds=0.05,
        max_attempts=2,
        client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
        executor=executor,
        backoff_seconds=0.0,
    )
    notifier.notify("https://hooks.example.test/in", _event())
    executor.shutdown(wait=True)
    assert len(calls) == 2
