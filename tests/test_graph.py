"""Specification for story graph validation.

Not implemented yet — see `tests/README.md` for the xfail convention.
"""

from __future__ import annotations

import pytest

from cyoa.engine.graph import Severity, reachable_from, validate_story
from cyoa.engine.models import Choice, Passage, Story

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="graph validation not implemented — delete this marker when it is",
)


def test_a_sound_story_has_no_issues(tiny_story: Story) -> None:
    assert validate_story(tiny_story) == []


def test_reachable_from_walks_the_whole_graph(tiny_story: Story) -> None:
    assert reachable_from(tiny_story) == {"start", "door", "window"}


def test_dangling_target_is_an_error(tiny_story: Story) -> None:
    tiny_story.passages["start"].choices[0].target = "missing"

    issues = validate_story(tiny_story)

    assert [i.code for i in issues] == ["dangling_target"]
    assert issues[0].severity is Severity.ERROR
    assert issues[0].passage_id == "start"


def test_missing_start_is_an_error() -> None:
    story = Story(
        slug="s",
        title="S",
        start="nowhere",
        passages={"somewhere": Passage(id="somewhere", body="Hello.")},
    )

    assert any(i.code == "missing_start" for i in validate_story(story))


def test_unreachable_passage_is_a_warning(tiny_story: Story) -> None:
    tiny_story.passages["orphan"] = Passage(id="orphan", body="Nobody comes here.")

    issues = validate_story(tiny_story)
    unreachable = [i for i in issues if i.code == "unreachable_passage"]

    assert [i.passage_id for i in unreachable] == ["orphan"]
    assert unreachable[0].severity is Severity.WARNING


def test_all_issues_are_reported_in_one_pass(tiny_story: Story) -> None:
    """An author should see every problem at once, not one per run."""
    tiny_story.passages["start"].choices[0].target = "missing"
    tiny_story.passages["orphan"] = Passage(
        id="orphan", choices=[Choice(text="Nowhere", target="also_missing")]
    )

    codes = {i.code for i in validate_story(tiny_story)}

    assert {"dangling_target", "unreachable_passage"} <= codes
