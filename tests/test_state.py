"""Tests for play state and passage transitions."""

from __future__ import annotations

import pytest

from cyoa.engine.models import Choice, Passage, Story
from cyoa.engine.state import advance, begin


def test_begin_positions_the_session_at_the_start_passage(tiny_story: Story) -> None:
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    assert session.current_passage_id == "start"
    assert session.story_slug == "tiny"
    assert session.history == []


def test_begin_records_every_participant(tiny_story: Story) -> None:
    """Sessions are participant-plural from the start, even though v1 only ever passes one."""
    session = begin(tiny_story, ["reader-1", "reader-2"], session_id="s1")

    assert session.participants == ["reader-1", "reader-2"]


def test_begin_rejects_a_start_that_does_not_exist() -> None:
    story = Story(
        slug="broken",
        title="Broken",
        start="nowhere",
        passages={"somewhere": Passage(id="somewhere", body="Hello.")},
    )

    with pytest.raises(ValueError):
        begin(story, ["reader-1"], session_id="s1")


def test_advance_moves_to_the_chosen_target(tiny_story: Story) -> None:
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    moved = advance(session, tiny_story, 0)

    assert moved.current_passage_id == "door"


def test_advance_records_where_the_reader_came_from(tiny_story: Story) -> None:
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    moved = advance(advance(session, tiny_story, 0), tiny_story, 0)

    assert moved.history == ["start", "door"]
    assert moved.current_passage_id == "window"


def test_advance_does_not_mutate_the_session_it_was_given(tiny_story: Story) -> None:
    """Immutable transitions are what make undo, replay, and preview free."""
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    advance(session, tiny_story, 0)

    assert session.current_passage_id == "start"
    assert session.history == []


def test_advance_preserves_session_identity(tiny_story: Story) -> None:
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    moved = advance(session, tiny_story, 0)

    assert moved.id == session.id
    assert moved.story_slug == session.story_slug
    assert moved.participants == session.participants
    assert moved.created_at == session.created_at


@pytest.mark.parametrize("choice_index", [2, 99])
def test_advance_rejects_a_choice_index_past_the_end(tiny_story: Story, choice_index: int) -> None:
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    with pytest.raises(ValueError):
        advance(session, tiny_story, choice_index)


def test_advance_rejects_a_negative_choice_index(tiny_story: Story) -> None:
    """A negative index would silently index from the end and 'work'."""
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    with pytest.raises(ValueError):
        advance(session, tiny_story, -1)


def test_advance_rejects_a_choice_from_an_ending(tiny_story: Story) -> None:
    session = begin(tiny_story, ["reader-1"], session_id="s1")
    ending = advance(session, tiny_story, 1)

    assert ending.current_passage_id == "window"
    with pytest.raises(ValueError):
        advance(ending, tiny_story, 0)


def test_advance_rejects_a_choice_whose_target_is_missing(tiny_story: Story) -> None:
    """Stories are validated at load time, so this should be unreachable — but a
    dangling target must fail loudly rather than strand a reader mid-story."""
    tiny_story.passages["start"].choices[0] = Choice(text="Nowhere", target="missing")
    session = begin(tiny_story, ["reader-1"], session_id="s1")

    with pytest.raises(ValueError):
        advance(session, tiny_story, 0)
