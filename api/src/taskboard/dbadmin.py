"""Database administration run by the migration step with the owner account.

The API itself connects as a separate, least-privilege role that can only read and write rows in
the application tables: it cannot create, alter or drop anything, and cannot see the migration
bookkeeping table.
"""

import os
import re
from pathlib import Path
from typing import Final

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql

APP_ROLE: Final = "taskboard_app"
_ROLE_PATTERN: Final = re.compile(r"^[a-z_][a-z0-9_]{2,62}$")


def libpq_url(url: str) -> str:
    """Turn a SQLAlchemy URL (``postgresql+psycopg://``) into one libpq accepts."""
    return re.sub(r"^postgresql\+psycopg://", "postgresql://", url, count=1)


def run_migrations(owner_url: str, alembic_ini: Path | None = None) -> None:
    """Apply every Alembic migration with the owner account."""
    ini = alembic_ini or Path(os.environ.get("ALEMBIC_CONFIG", "alembic.ini"))
    os.environ["MIGRATION_DATABASE_URL"] = owner_url
    command.upgrade(Config(str(ini)), "head")


def ensure_app_role(owner_url: str, password: str, role: str = APP_ROLE) -> None:
    """Create or update the application role and grant it row-level access only."""
    if not _ROLE_PATTERN.fullmatch(role):
        raise ValueError("invalid role name")
    if len(password) < 16:
        raise ValueError("the application role password must be at least 16 characters")
    ident = sql.Identifier(role)
    with psycopg.connect(libpq_url(owner_url), autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
        options = sql.SQL(
            "LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}"
        ).format(sql.Literal(password))
        if exists:
            conn.execute(sql.SQL("ALTER ROLE {} WITH {}").format(ident, options))
        else:
            conn.execute(sql.SQL("CREATE ROLE {} WITH {}").format(ident, options))
        database = conn.execute("SELECT current_database()").fetchone()
        if database is None:
            raise RuntimeError("could not determine the current database")
        conn.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(str(database[0])), ident
            )
        )
        conn.execute(sql.SQL("REVOKE CREATE ON SCHEMA public FROM {}").format(ident))
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(ident))
        conn.execute(
            sql.SQL(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}"
            ).format(ident)
        )
        conn.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
            ).format(ident)
        )
        has_version_table = conn.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'alembic_version'"
        ).fetchone()
        if has_version_table:
            conn.execute(sql.SQL("REVOKE ALL ON TABLE alembic_version FROM {}").format(ident))
