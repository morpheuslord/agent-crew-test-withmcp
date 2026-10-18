"""FastAPI dependencies: per-request services, caller identity and service authentication."""

import hmac
import ipaddress
import logging
from collections.abc import Iterator
from typing import Annotated, Final

from fastapi import Depends, Header, Request

from taskboard.composition import Infrastructure, RequestServices
from taskboard.domain.entities import User
from taskboard.domain.errors import AuthenticationRequiredError

logger = logging.getLogger("taskboard.auth")

SERVICE_AUTH_HEADER: Final = "X-Service-Token"
CLIENT_IP_HEADER: Final = "X-Client-IP"


def get_infra(request: Request) -> Infrastructure:
    infra: Infrastructure = request.app.state.infra
    return infra


def get_services(infra: Annotated[Infrastructure, Depends(get_infra)]) -> Iterator[RequestServices]:
    """One database session per request; anything not committed by a service is rolled back."""
    with infra.session_factory() as session:
        try:
            yield RequestServices(infra, session)
        finally:
            session.rollback()


Services = Annotated[RequestServices, Depends(get_services)]


def require_service_auth(
    infra: Annotated[Infrastructure, Depends(get_infra)],
    x_service_token: Annotated[str | None, Header(alias=SERVICE_AUTH_HEADER)] = None,
) -> None:
    """Only the UI server, which holds the shared secret, may call the API."""
    expected = infra.settings.service_auth_secret.get_secret_value().encode()
    supplied = (x_service_token or "").encode()
    if not hmac.compare_digest(supplied, expected):
        logger.warning("service authentication failed")
        raise AuthenticationRequiredError("Service authentication required.")


def bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization:
        raise AuthenticationRequiredError()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or len(token) > 200:
        raise AuthenticationRequiredError()
    return token.strip()


BearerToken = Annotated[str, Depends(bearer_token)]


def current_user(services: Services, token: BearerToken) -> User:
    return services.auth.authenticate(token)


CurrentUser = Annotated[User, Depends(current_user)]


def client_ip(
    request: Request,
    x_client_ip: Annotated[str | None, Header(alias=CLIENT_IP_HEADER)] = None,
) -> str:
    """The browser's IP as reported by the authenticated UI server, else the peer address."""
    if x_client_ip:
        try:
            return str(ipaddress.ip_address(x_client_ip.strip()))
        except ValueError:
            pass
    return request.client.host if request.client else "unknown"


ClientIp = Annotated[str, Depends(client_ip)]
