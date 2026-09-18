"""Tests for persistence: the engine, the schema, and the repository.

Two things are being pinned down here. The first is that a `PlaySession` comes
back out of SQLite as the same session that went in — including the JSON-backed
lists and the timezone SQLite does not store. The second is the boundary rule:
a repository speaks engine types, so `PlaySessionRow` never appears in anything
a caller receives.

Sessions under test are built with `begin` and `advance` rather than
constructed by hand, so what is being round-tripped is a session the engine
would actually produce.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Engine, inspect, select

from cyoa.engine.models import Story
from cyoa.engine.state import PlaySession, advance, begin
from cyoa.storage import PlaySessionRepository, create_engine_for, create_schema, session_scope
from cyoa.storage.models import PlaySessionRow


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """An engine over a throwaway database file, schema already created."""
    engine = create_engine_for(tmp_path / "cyoa.db")
    create_schema(engine)
    return engine


@pytest.fixture
def session(tiny_story: Story) -> PlaySession:
    """A play session as the engine would hand one over."""
    return begin(tiny_story, ["reader-1"], session_id="s1")


def _save(engine: Engine, play_session: PlaySession) -> None:
    """Save one session in a transaction of its own, as a request would."""
    with session_scope(engine) as db:
        PlaySessionRepository(db).save(play_session)


def _get(engine: Engine, session_id: str) -> PlaySession | None:
    """Read one session back in a *separate* transaction.

    Separate on purpose. Reading in the same session that wrote would be served
    from SQLAlchemy's identity map and never touch SQLite, which is exactly the
    round trip these tests exist to exercise.
    """
    with session_scope(engine) as db:
        return PlaySessionRepository(db).get(session_id)


def _row_count(engine: Engine) -> int:
    """How many rows are actually in the table, whatever the repository says."""
    with session_scope(engine) as db:
        return len(db.execute(select(PlaySessionRow)).all())


# --- engine and schema ------------------------------------------------------


def test_create_engine_for_creates_the_parent_directory(tmp_path: Path) -> None:
    """A fresh volume mount should work on first boot with no setup step."""
    db_path = tmp_path / "data" / "nested" / "cyoa.db"

    create_engine_for(db_path)

    assert db_path.parent.is_dir()


def test_create_schema_writes_the_database_file(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "cyoa.db"

    create_schema(create_engine_for(db_path))

    assert db_path.is_file()


def test_create_schema_creates_the_play_sessions_table(engine: Engine) -> None:
    assert "play_sessions" in inspect(engine).get_table_names()


def test_create_schema_leaves_existing_data_alone(engine: Engine, session: PlaySession) -> None:
    """`create_app()` runs it on every boot, so a restart must not cost a reader
    their place."""
    _save(engine, session)

    create_schema(engine)

    assert _get(engine, "s1") is not None


# --- the repository round trip ----------------------------------------------


def test_get_returns_none_for_a_session_that_was_never_saved(engine: Engine) -> None:
    assert _get(engine, "no-such-session") is None


def test_a_saved_session_comes_back(engine: Engine, session: PlaySession) -> None:
    _save(engine, session)

    stored = _get(engine, "s1")

    assert stored is not None
    assert stored.id == "s1"
    assert stored.story_slug == "tiny"
    assert stored.current_passage_id == "start"


def test_a_round_trip_preserves_participants(engine: Engine, tiny_story: Story) -> None:
    """A JSON column, read and written whole — and the list multiplayer needs."""
    _save(engine, begin(tiny_story, ["reader-1", "reader-2"], session_id="s1"))

    stored = _get(engine, "s1")

    assert stored is not None
    assert stored.participants == ["reader-1", "reader-2"]


def test_a_round_trip_preserves_history(
    engine: Engine, session: PlaySession, tiny_story: Story
) -> None:
    moved = advance(advance(session, tiny_story, 0), tiny_story, 0)

    _save(engine, moved)

    stored = _get(engine, "s1")
    assert stored is not None
    assert stored.history == ["start", "door"]


def test_an_empty_history_round_trips_as_an_empty_list(
    engine: Engine, session: PlaySession
) -> None:
    """Not as None — a fresh session has been nowhere, and the engine's
    `history` is a list either way."""
    _save(engine, session)

    stored = _get(engine, "s1")

    assert stored is not None
    assert stored.history == []


def test_a_session_comes_back_as_an_engine_type(engine: Engine, session: PlaySession) -> None:
    """The boundary rule: a row is how a session is written down, never what a
    caller is handed."""
    _save(engine, session)

    stored = _get(engine, "s1")

    assert isinstance(stored, PlaySession)


# --- saving the same session again ------------------------------------------


def test_saving_a_session_again_updates_it(
    engine: Engine, session: PlaySession, tiny_story: Story
) -> None:
    """A reader advancing saves the same id on every move."""
    _save(engine, session)

    _save(engine, advance(session, tiny_story, 0))

    stored = _get(engine, "s1")
    assert stored is not None
    assert stored.current_passage_id == "door"


def test_saving_a_session_again_does_not_add_a_row(
    engine: Engine, session: PlaySession, tiny_story: Story
) -> None:
    _save(engine, session)

    _save(engine, advance(session, tiny_story, 0))

    assert _row_count(engine) == 1


def test_two_stories_in_progress_do_not_evict_each_other(engine: Engine, tiny_story: Story) -> None:
    """ADR-010's promise, at the storage layer."""
    _save(engine, begin(tiny_story, ["reader-1"], session_id="first"))
    other = tiny_story.model_copy(update={"slug": "other"})
    _save(engine, begin(other, ["reader-1"], session_id="second"))

    first, second = _get(engine, "first"), _get(engine, "second")

    assert first is not None and first.story_slug == "tiny"
    assert second is not None and second.story_slug == "other"


# --- deleting ---------------------------------------------------------------


def test_delete_removes_a_session(engine: Engine, session: PlaySession) -> None:
    _save(engine, session)

    with session_scope(engine) as db:
        PlaySessionRepository(db).delete("s1")

    assert _get(engine, "s1") is None


def test_delete_is_a_no_op_for_a_session_that_is_not_there(engine: Engine) -> None:
    """Restart deletes whatever the cookie names, which may be long gone."""
    with session_scope(engine) as db:
        PlaySessionRepository(db).delete("no-such-session")


def test_delete_leaves_other_sessions_alone(engine: Engine, tiny_story: Story) -> None:
    _save(engine, begin(tiny_story, ["reader-1"], session_id="keep"))
    _save(engine, begin(tiny_story, ["reader-2"], session_id="drop"))

    with session_scope(engine) as db:
        PlaySessionRepository(db).delete("drop")

    assert _get(engine, "keep") is not None


# --- timestamps -------------------------------------------------------------


def test_a_timestamp_comes_back_with_its_timezone(engine: Engine, session: PlaySession) -> None:
    """SQLite's DATETIME drops the offset. The repository re-attaches UTC."""
    _save(engine, session)

    stored = _get(engine, "s1")

    assert stored is not None
    assert stored.created_at.tzinfo is not None
    assert stored.updated_at.tzinfo is not None


def test_a_restored_timestamp_can_be_compared_to_now(engine: Engine, session: PlaySession) -> None:
    """The failure this prevents is not a wrong offset, it is a `TypeError`:
    a naive datetime out of SQLite cannot be compared with `datetime.now(UTC)`,
    and a resumed session would raise on any code that tried."""
    _save(engine, session)

    stored = _get(engine, "s1")

    assert stored is not None
    assert stored.created_at <= datetime.now(UTC)


def test_a_restored_timestamp_keeps_its_value(engine: Engine, session: PlaySession) -> None:
    """Re-attaching a timezone must not shift the instant it names, and the
    round trip must not quietly round off the microseconds either."""
    _save(engine, session)

    stored = _get(engine, "s1")

    assert stored is not None
    assert stored.created_at == session.created_at


# --- transaction scope ------------------------------------------------------


def test_session_scope_commits_on_the_way_out(engine: Engine, session: PlaySession) -> None:
    with session_scope(engine) as db:
        PlaySessionRepository(db).save(session)

    assert _get(engine, "s1") is not None


def test_session_scope_rolls_back_when_the_block_raises(
    engine: Engine, session: PlaySession
) -> None:
    """A request that fails half way through should leave no partial progress."""
    with pytest.raises(RuntimeError), session_scope(engine) as db:
        PlaySessionRepository(db).save(session)
        raise RuntimeError("the request failed after saving")

    assert _get(engine, "s1") is None


def test_session_scope_re_raises_the_original_error(engine: Engine) -> None:
    """Rolling back must not swallow what went wrong."""
    with pytest.raises(RuntimeError, match="the request failed"), session_scope(engine):
        raise RuntimeError("the request failed")


def test_a_rolled_back_scope_leaves_earlier_work_intact(
    engine: Engine, session: PlaySession, tiny_story: Story
) -> None:
    """Rollback is scoped to its own transaction, not the database."""
    _save(engine, session)

    with pytest.raises(RuntimeError), session_scope(engine) as db:
        PlaySessionRepository(db).save(advance(session, tiny_story, 0))
        raise RuntimeError("the request failed after saving")

    stored = _get(engine, "s1")
    assert stored is not None
    assert stored.current_passage_id == "start"
