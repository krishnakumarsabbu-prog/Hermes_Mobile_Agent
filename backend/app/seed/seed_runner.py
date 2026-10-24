"""Seed runner: python -m app.seed.seed_runner [--reset].

Idempotent by default. The --reset flag must be passed explicitly to wipe and
reseed; it never runs automatically on ordinary startup.
"""
from __future__ import annotations

import argparse
import sys

from app.core.database import get_engine, session_scope
from app.core.logging import configure_logging
from app.models.base import Base
from app.seed.generator import generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the Hermes simulation database.")
    parser.add_argument("--reset", action="store_true", help="Erase all data before seeding. Destructive and deliberate.")
    args = parser.parse_args(argv)

    configure_logging()

    # Ensure schema exists (migrations are the preferred path, but ensure
    # tables are present so seeding works even without an explicit migrate step).
    Base.metadata.create_all(get_engine())

    with session_scope() as session:
        counts = generate(session, reset=args.reset)

    print("Seed complete. Row counts:")
    for key, value in counts.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
