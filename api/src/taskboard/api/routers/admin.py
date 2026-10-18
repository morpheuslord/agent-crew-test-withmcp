"""Admin-only endpoints. The role check lives in the services, not here."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from taskboard.api.deps import CurrentUser, Services
from taskboard.api.schemas.accounts import AdminUserUpdate, UserOut, UserPage
from taskboard.api.schemas.common import PageParams
from taskboard.api.schemas.work import ActivityOut, ActivityPage

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    paging: Annotated[PageParams, Query()], services: Services, user: CurrentUser
) -> UserPage:
    page = services.user_admin.list_users(user, paging.page, paging.page_size)
    return UserPage(
        items=[UserOut.model_validate(u) for u in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID, body: AdminUserUpdate, services: Services, user: CurrentUser
) -> UserOut:
    updated = services.user_admin.update_user(
        user, user_id, role=body.role, is_active=body.is_active
    )
    return UserOut.model_validate(updated)


@router.get("/cache/stats")
def cache_stats(services: Services, user: CurrentUser) -> dict[str, object]:
    """Hit, miss and error counters per cache key family, for this API process."""
    return services.user_admin.cache_stats(user)


@router.get("/activity")
def global_activity(
    paging: Annotated[PageParams, Query()], services: Services, user: CurrentUser
) -> ActivityPage:
    page = services.activity.global_feed(user, paging.page, paging.page_size)
    return ActivityPage(
        items=[ActivityOut.model_validate(e) for e in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )
