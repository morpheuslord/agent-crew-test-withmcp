"""Repositories for users, sessions, password reset tokens and the mail outbox."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from taskboard.domain.entities import OutboxMessage, Page, User, UserCredentials
from taskboard.domain.enums import Role
from taskboard.models.tables import OutboxRow, PasswordResetTokenRow, SessionRow, UserRow
from taskboard.repositories.sqlalchemy.mappers import to_user


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, email: str, display_name: str, password_hash: str, role: Role) -> User:
        row = UserRow(
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            role=role.value,
            is_active=True,
        )
        self._s.add(row)
        self._s.flush()
        self._s.refresh(row)
        return to_user(row)

    def get(self, user_id: UUID) -> User | None:
        row = self._s.get(UserRow, user_id)
        return to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self._s.scalar(select(UserRow).where(UserRow.email == email))
        return to_user(row) if row else None

    def get_credentials(self, email: str) -> UserCredentials | None:
        row = self._s.scalar(select(UserRow).where(UserRow.email == email))
        return UserCredentials(user=to_user(row), password_hash=row.password_hash) if row else None

    def get_password_hash(self, user_id: UUID) -> str | None:
        return self._s.scalar(select(UserRow.password_hash).where(UserRow.id == user_id))

    def set_password_hash(self, user_id: UUID, password_hash: str) -> None:
        self._s.execute(
            update(UserRow).where(UserRow.id == user_id).values(password_hash=password_hash)
        )

    def update(
        self, user_id: UUID, *, role: Role | None = None, is_active: bool | None = None
    ) -> User | None:
        row = self._s.get(UserRow, user_id)
        if row is None:
            return None
        if role is not None:
            row.role = role.value
        if is_active is not None:
            row.is_active = is_active
        self._s.flush()
        self._s.refresh(row)
        return to_user(row)

    def list(self, page: int, page_size: int) -> Page[User]:
        total = self._s.scalar(select(func.count()).select_from(UserRow)) or 0
        rows = self._s.scalars(
            select(UserRow)
            .order_by(UserRow.created_at, UserRow.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return Page(tuple(to_user(r) for r in rows), total, page, page_size)


class SqlSessionRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._s.add(SessionRow(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
        self._s.flush()

    def find_user(self, token_hash: str, now: datetime) -> User | None:
        row = self._s.scalar(
            select(UserRow)
            .join(SessionRow, SessionRow.user_id == UserRow.id)
            .where(
                SessionRow.token_hash == token_hash,
                SessionRow.expires_at > now,
                UserRow.is_active.is_(True),
            )
        )
        return to_user(row) if row else None

    def delete(self, token_hash: str) -> None:
        self._s.execute(delete(SessionRow).where(SessionRow.token_hash == token_hash))

    def delete_for_user(self, user_id: UUID) -> None:
        self._s.execute(delete(SessionRow).where(SessionRow.user_id == user_id))


class SqlResetTokenRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._s.add(
            PasswordResetTokenRow(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        )
        self._s.flush()

    def consume(self, token_hash: str, now: datetime) -> UUID | None:
        # A single UPDATE ... RETURNING makes the token single-use even under concurrency.
        return self._s.scalar(
            update(PasswordResetTokenRow)
            .where(
                PasswordResetTokenRow.token_hash == token_hash,
                PasswordResetTokenRow.used_at.is_(None),
                PasswordResetTokenRow.expires_at > now,
            )
            .values(used_at=now)
            .returning(PasswordResetTokenRow.user_id)
        )

    def invalidate_for_user(self, user_id: UUID, now: datetime) -> None:
        self._s.execute(
            update(PasswordResetTokenRow)
            .where(
                PasswordResetTokenRow.user_id == user_id,
                PasswordResetTokenRow.used_at.is_(None),
            )
            .values(used_at=now)
        )


class SqlOutboxRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, to_email: str, subject: str, body: str) -> OutboxMessage:
        row = OutboxRow(to_email=to_email, subject=subject, body=body)
        self._s.add(row)
        self._s.flush()
        self._s.refresh(row)
        return OutboxMessage(row.id, row.to_email, row.subject, row.body, row.created_at)

    def list_for(self, to_email: str) -> Sequence[OutboxMessage]:
        rows = self._s.scalars(
            select(OutboxRow).where(OutboxRow.to_email == to_email).order_by(OutboxRow.created_at)
        )
        return [OutboxMessage(r.id, r.to_email, r.subject, r.body, r.created_at) for r in rows]
