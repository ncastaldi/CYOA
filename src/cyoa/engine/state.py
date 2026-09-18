"""Play state and the transitions between passages.

State transitions are pure functions over a `PlaySession` and a `Story`. They
neither read nor write persistence — `cyoa.storage` saves and loads sessions,
this module decides what a session becomes next. That split is what lets the
same engine drive a web request, a future CLI client, or a test.

Multiplayer foundation
----------------------
Position belongs to the *session*, not to a reader. A `PlaySession` carries a
list of participants and one current passage, so v1 (one participant) and the
likeliest multiplayer shape (several readers moving through one book together,
agreeing on each choice) are the same data structure.

This is an assumption, not a guarantee: a mode where readers move through the
story independently would need per-participant positions, and that is a schema
change rather than a free extension. Recorded as an open question in
`CLAUDE.md` so it gets decided deliberately.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from cyoa.engine.models import Story

#: Identifies a reader within a session. Opaque on purpose — v1 mints an
#: anonymous id per browser; an authenticated user id can take its place later
#: without the engine noticing.
ParticipantId = str


class PlaySession(BaseModel):
    """One run through one story by one or more readers."""

    id: str
    story_slug: str
    current_passage_id: str
    participants: list[ParticipantId] = Field(default_factory=list)
    history: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


def begin(story: Story, participants: list[ParticipantId], *, session_id: str) -> PlaySession:
    """Open a new session positioned at `story.start`.

    Raises:
        ValueError: if `story.start` names a passage the story does not have.
            Callers should validate stories at load time so this never fires
            at read time.
    """
    raise NotImplementedError


def advance(session: PlaySession, story: Story, choice_index: int) -> PlaySession:
    """Return a new session moved along the chosen branch.

    Does not mutate `session` — returns a new one with the previous passage
    appended to `history`. Keeping transitions immutable means an undo, a
    replay, or a "what if" preview in a future editor costs nothing extra.

    Raises:
        ValueError: if `choice_index` is out of range for the current passage,
            or if the chosen target does not exist in `story`.
    """
    raise NotImplementedError
