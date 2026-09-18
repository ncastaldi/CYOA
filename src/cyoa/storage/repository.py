"""Repositories — the only code in CYOA that reads or writes the database.

Repositories speak in engine types. A caller hands over a `PlaySession` and
gets a `PlaySession` back; the fact that a row, a column, or SQLAlchemy exists
at all stops here. Routes never see a `PlaySessionRow`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session as DbSession

from cyoa.engine.state import PlaySession
from cyoa.storage.models import PlaySessionRow


class PlaySessionRepository:
    """Loads and stores reader progress."""

    def __init__(self, db: DbSession) -> None:
        self.db = db

    def get(self, session_id: str) -> PlaySession | None:
        """Return the session with this id, or None if there is no such session."""
        row = self.db.get(PlaySessionRow, session_id)
        return None if row is None else _to_domain(row)

    def save(self, session: PlaySession) -> None:
        """Insert or update `session`."""
        # merge rather than add: a reader advancing through a story saves the
        # same id on every move, and the route should not have to know whether
        # this is the first one.
        self.db.merge(_to_row(session))

    def delete(self, session_id: str) -> None:
        """Remove a session. Used when a reader restarts a story."""
        row = self.db.get(PlaySessionRow, session_id)
        if row is not None:
            self.db.delete(row)


def _to_row(session: PlaySession) -> PlaySessionRow:
    """Write a domain session down as a row."""
    return PlaySessionRow(
        id=session.id,
        story_slug=session.story_slug,
        current_passage_id=session.current_passage_id,
        participants=list(session.participants),
        history=list(session.history),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _to_domain(row: PlaySessionRow) -> PlaySession:
    """Read a row back as a domain session."""
    return PlaySession(
        id=row.id,
        story_slug=row.story_slug,
        current_passage_id=row.current_passage_id,
        participants=list(row.participants),
        history=list(row.history),
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def _as_utc(value: datetime) -> datetime:
    """Re-attach UTC to a timestamp SQLite handed back without a timezone.

    The engine deals only in aware datetimes; SQLite's DATETIME drops the
    offset. Without this, a session read back from disk would compare against
    a fresh `datetime.now(UTC)` and raise.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
