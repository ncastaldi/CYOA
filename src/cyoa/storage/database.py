"""Database engine and session management.

SQLite, one file on a mounted volume. Chosen because it backs up with `cp` and
needs no second container — see the ADR-003 entry in `CLAUDE.md`.

Everything here is written against SQLAlchemy rather than `sqlite3` directly,
so that if multiplayer concurrency ever outgrows SQLite, moving to Postgres is
a connection-string change plus a migration, not a rewrite of every query.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session


def create_engine_for(db_path: Path) -> Engine:
    """Build the SQLAlchemy engine for the SQLite file at `db_path`.

    Creates the parent directory if it does not exist, so a fresh volume mount
    works on first boot without a setup step.
    """
    raise NotImplementedError


def create_schema(engine: Engine) -> None:
    """Create any missing tables.

    v1 has no migration tool — the schema is small and the app is new, so
    `create_all` is honest about where the project is. When the first schema
    change lands that cannot be expressed as an added nullable column, this is
    where Alembic goes in.
    """
    raise NotImplementedError


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Yield a transactional session, committing on success and rolling back on error."""
    raise NotImplementedError
