"""SQLAlchemy table definitions.

These types describe rows, not the domain. The engine's `PlaySession` is the
domain object; `PlaySessionRow` is how one gets written down. `repository.py`
translates between them, so a change of database — or of persistence entirely —
stops at the edge of this package.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all CYOA tables."""


class PlaySessionRow(Base):
    """A reader's progress through one story.

    `participants` and `history` are JSON columns rather than child tables.
    That is a deliberate v1 simplification: they are read and written whole,
    never queried into. If multiplayer later needs to ask "which sessions is
    this reader in", participants earns a real table — the repository absorbs
    that change without the engine noticing.
    """

    __tablename__ = "play_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    story_slug: Mapped[str] = mapped_column(String, index=True)
    current_passage_id: Mapped[str] = mapped_column(String)
    participants: Mapped[list[str]] = mapped_column(JSON, default=list)
    history: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
