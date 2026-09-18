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

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from cyoa.storage.models import Base


def create_engine_for(db_path: Path) -> Engine:
    """Build the SQLAlchemy engine for the SQLite file at `db_path`.

    Creates the parent directory if it does not exist, so a fresh volume mount
    works on first boot without a setup step.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{db_path}",
        # FastAPI runs sync handlers in a worker threadpool, so a pooled
        # connection is reached from whichever thread picks up the request.
        # Each request still gets its own Session, which is what keeps the
        # transactions separate.
        connect_args={"check_same_thread": False},
    )


def create_schema(engine: Engine) -> None:
    """Create any missing tables.

    v1 has no migration tool — the schema is small and the app is new, so
    `create_all` is honest about where the project is. When the first schema
    change lands that cannot be expressed as an added nullable column, this is
    where Alembic goes in.
    """
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Yield a transactional session, committing on success and rolling back on error."""
    # expire_on_commit=False: the caller may still read what it just saved
    # after the scope commits, and a refresh against a closed session would
    # fail. Repositories hand back engine types anyway, never live rows.
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
