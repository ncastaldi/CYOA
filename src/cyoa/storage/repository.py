"""Repositories — the only code in CYOA that reads or writes the database.

Repositories speak in engine types. A caller hands over a `PlaySession` and
gets a `PlaySession` back; the fact that a row, a column, or SQLAlchemy exists
at all stops here. Routes never see a `PlaySessionRow`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session as DbSession

from cyoa.engine.state import PlaySession


class PlaySessionRepository:
    """Loads and stores reader progress."""

    def __init__(self, db: DbSession) -> None:
        self.db = db

    def get(self, session_id: str) -> PlaySession | None:
        """Return the session with this id, or None if there is no such session."""
        raise NotImplementedError

    def save(self, session: PlaySession) -> None:
        """Insert or update `session`."""
        raise NotImplementedError

    def delete(self, session_id: str) -> None:
        """Remove a session. Used when a reader restarts a story."""
        raise NotImplementedError
