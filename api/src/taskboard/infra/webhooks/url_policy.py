"""Validation of user-supplied webhook URLs, so the API cannot be used as an SSRF proxy."""

import ipaddress
import socket
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final
from urllib.parse import SplitResult, urlsplit

from taskboard.domain.errors import ValidationFailedError

MAX_URL_LENGTH: Final = 2048

# Ranges that are_global misses or that we never want to reach even if marked global.
_EXTRA_BLOCKED: Final = (
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("64:ff9b::/96"),  # NAT64 can embed private IPv4
    ipaddress.ip_network("2002::/16"),  # 6to4 can embed private IPv4
)

Resolver = Callable[[str, int], Sequence[str]]


def system_resolver(host: str, port: int) -> Sequence[str]:
    """Resolve every address for ``host`` with the system resolver."""
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return [str(info[4][0]) for info in infos]


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """A webhook destination pinned to one validated address."""

    scheme: str
    host: str
    port: int
    address: str
    path: str

    @property
    def connect_url(self) -> str:
        """URL that connects to the validated address instead of re-resolving the host name."""
        ip = ipaddress.ip_address(self.address)
        literal = f"[{self.address}]" if ip.version == 6 else self.address
        return f"{self.scheme}://{literal}:{self.port}{self.path}"

    @property
    def host_header(self) -> str:
        default = 443 if self.scheme == "https" else 80
        return self.host if self.port == default else f"{self.host}:{self.port}"


class WebhookUrlPolicy:
    """Checks a URL when it is saved, and again (with DNS resolution) before every delivery."""

    def __init__(
        self,
        *,
        allow_http: bool,
        allow_private: bool,
        resolver: Resolver = system_resolver,
    ) -> None:
        self._allow_http = allow_http
        self._allow_private = allow_private
        self._resolver = resolver

    def _parse(self, url: str) -> SplitResult:
        if len(url) > MAX_URL_LENGTH:
            raise ValidationFailedError("Webhook URL is too long.")
        try:
            parts = urlsplit(url.strip())
            _ = parts.port  # raises ValueError for a malformed port
        except ValueError as exc:
            raise ValidationFailedError("Webhook URL is not a valid URL.") from exc
        allowed = {"https", "http"} if self._allow_http else {"https"}
        if parts.scheme not in allowed:
            raise ValidationFailedError("Webhook URL must use https.")
        if not parts.hostname:
            raise ValidationFailedError("Webhook URL must include a host.")
        if parts.username or parts.password:
            raise ValidationFailedError("Webhook URL must not contain credentials.")
        return parts

    def _is_public(self, address: str) -> bool:
        ip = ipaddress.ip_address(address)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        if any(ip in net for net in _EXTRA_BLOCKED):
            return False
        return ip.is_global and not ip.is_multicast

    def validate(self, url: str) -> str:
        """Static checks for storage time. Literal non-public IPs are rejected immediately."""
        parts = self._parse(url)
        host = parts.hostname or ""
        try:
            literal = ipaddress.ip_address(host)
        except ValueError:
            literal = None
        if literal is not None and not self._allow_private and not self._is_public(host):
            raise ValidationFailedError("Webhook URL must point to a public address.")
        if not self._allow_private and host.lower() in {"localhost", "localhost.localdomain"}:
            raise ValidationFailedError("Webhook URL must point to a public address.")
        return parts.geturl()

    def resolve(self, url: str) -> ResolvedTarget:
        """Resolve the host and return a target pinned to an address that passed the checks."""
        parts = self._parse(url)
        host = parts.hostname or ""
        port = parts.port or (443 if parts.scheme == "https" else 80)
        try:
            addresses = list(self._resolver(host, port))
        except OSError as exc:
            raise ValidationFailedError("Webhook host could not be resolved.") from exc
        if not addresses:
            raise ValidationFailedError("Webhook host could not be resolved.")
        if not self._allow_private and not all(self._is_public(a) for a in addresses):
            raise ValidationFailedError("Webhook URL resolves to a non-public address.")
        path = parts.path or "/"
        if parts.query:
            path = f"{path}?{parts.query}"
        return ResolvedTarget(parts.scheme, host, port, addresses[0], path)
