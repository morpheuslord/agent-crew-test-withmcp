"""Management commands.

``taskboard-admin create-admin`` creates (or promotes) the first admin from the
``ADMIN_EMAIL`` and ``ADMIN_PASSWORD`` environment variables. There are no defaults.
"""

import argparse
import os
import sys
from collections.abc import Sequence

from taskboard.composition import RequestServices, build_infrastructure
from taskboard.config import get_settings
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskboard-admin")
    parser.add_argument("command", choices=["create-admin"])
    args = parser.parse_args(argv)
    if args.command == "create-admin":
        return create_admin()
    return 2  # argparse already rejects unknown commands


if __name__ == "__main__":
    raise SystemExit(main())
