"""Tests for the internal story model.

These run for real — `models.py` is implemented.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cyoa.engine.models import Choice, Passage, Story


def test_passage_without_choices_is_an_ending() -> None:
    assert Passage(id="fin", body="Done.").is_ending


def test_passage_with_choices_is_not_an_ending() -> None:
    passage = Passage(id="fork", choices=[Choice(text="Left", target="left")])
    assert not passage.is_ending


def test_story_passage_lookup_returns_none_for_unknown_id(tiny_story: Story) -> None:
    assert tiny_story.passage("start") is not None
    assert tiny_story.passage("nowhere") is None


@pytest.mark.parametrize("field", ["text", "target"])
def test_choice_rejects_empty_strings(field: str) -> None:
    values = {"text": "Go", "target": "there", field: ""}
    with pytest.raises(ValidationError):
        Choice(**values)


def test_story_requires_a_start_passage_id() -> None:
    with pytest.raises(ValidationError):
        Story(slug="s", title="S", start="")
