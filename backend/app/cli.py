from __future__ import annotations

import argparse
import os
import sys

from app.db.session import SessionLocal
from app.models.entities import User  # noqa: F401  ensure models imported
from app.services.auth_service import bootstrap_admin
from app.services.errors import AppError


def cmd_bootstrap_admin(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        user = bootstrap_admin(db, args.email, args.password, args.full_name)
        print(f"Administrator created: {user.email} id={user.id}")
        return 0
    except AppError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    finally:
        db.close()


def cmd_seed_dev(args: argparse.Namespace) -> int:
    if os.environ.get("ALLOW_DEV_SEED", "").lower() not in {"1", "true", "yes"}:
        print("Refusing to seed. Set ALLOW_DEV_SEED=true to enable development seed data.", file=sys.stderr)
        return 1
    from app.services.dev_seed import seed_development_data

    db = SessionLocal()
    try:
        seed_development_data(db)
        print("Development seed data inserted. This is NOT production activity.")
        return 0
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(prog="campusmatch")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bootstrap-admin", help="Create the first administrator (no public signup)")
    b.add_argument("--email", required=True)
    b.add_argument("--password", required=True)
    b.add_argument("--full-name", default="Placement Administrator")
    b.set_defaults(func=cmd_bootstrap_admin)
    s = sub.add_parser("seed-dev", help="Insert labeled development fixtures (never for production)")
    s.set_defaults(func=cmd_seed_dev)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
