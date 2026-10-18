"""Management commands.

``taskboard-admin create-admin`` creates (or promotes) the first admin from the
``ADMIN_EMAIL`` and ``ADMIN_PASSWORD`` environment variables. There are no defaults.

``taskboard-admin migrate`` applies the Alembic migrations with the owner account from
``MIGRATION_DATABASE_URL`` and, when ``DB_APP_PASSWORD`` is set, creates or updates the
least-privilege role the API connects as.
"""

import argparse
import os
import sys
from collections.abc import Sequence

from taskboard.composition import RequestServices, build_infrastructure
from taskboard.config import get_settings
from taskboard.dbadmin import ensure_app_role, run_migrations
from taskboard.domain.errors import DomainError
from taskboard.logging_setup import configure_logging


def create_admin() -> int:
    email = os.environ.get("ADMIN_EMAIL", "")
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not email or not password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be set.", file=sys.stderr)
        return 2
    settings = get_settings()
    configure_logging(settings.log_level)
    infra = build_infrastructure(settings)
    try:
        with infra.session_factory() as session:
            user = RequestServices(infra, session).provisioner.ensure_admin(email, password)
    except DomainError as exc:
        print(f"Could not create admin: {exc.message}", file=sys.stderr)
        return 1
    finally:
        infra.close()
    print(f"Admin ready: {user.email}")
    return 0


def migrate() -> int:
    owner_url = os.environ.get("MIGRATION_DATABASE_URL", "")
    if not owner_url:
        print("MIGRATION_DATABASE_URL must be set.", file=sys.stderr)
        return 2
    run_migrations(owner_url)
    app_password = os.environ.get("DB_APP_PASSWORD", "")
    if app_password:
        try:
            ensure_app_role(owner_url, app_password)
        except ValueError as exc:
            print(f"Could not configure the application role: {exc}", file=sys.stderr)
            return 1
        print("Migrations applied; application role configured.")
    else:
        print("Migrations applied.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskboard-admin")
    parser.add_argument("command", choices=["create-admin", "migrate"])
    args = parser.parse_args(argv)
    if args.command == "migrate":
        return migrate()
    return create_admin()


if __name__ == "__main__":
    raise SystemExit(main())
