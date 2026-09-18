"""Specification for the Markdown + frontmatter parser.

`MarkdownStoryParser` is not implemented yet, so every test here is marked
xfail against `NotImplementedError`. They are the spec, written first. See
`tests/README.md` for why the marker is strict.
"""

from __future__ import annotations

import pytest

from cyoa.engine.markdown_parser import MarkdownStoryParser
from cyoa.engine.parser import StoryParseError

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError,
    strict=True,
    reason="MarkdownStoryParser not implemented — delete this marker when it is",
)


def test_parses_story_metadata_from_frontmatter(tiny_source: str) -> None:
    story = MarkdownStoryParser().parse(tiny_source, slug="tiny")

    assert story.slug == "tiny"
    assert story.title == "Tiny"
    assert story.author == "Test Suite"
    assert story.start == "start"


def test_parses_every_passage(tiny_source: str) -> None:
    story = MarkdownStoryParser().parse(tiny_source, slug="tiny")

    assert set(story.passages) == {"start", "door", "window"}


def test_parses_choices_in_document_order(tiny_source: str) -> None:
    story = MarkdownStoryParser().parse(tiny_source, slug="tiny")

    assert [c.text for c in story.passages["start"].choices] == [
        "Open the door",
        "Climb out the window",
    ]
    assert [c.target for c in story.passages["start"].choices] == ["door", "window"]


def test_choice_markup_is_stripped_from_passage_body(tiny_source: str) -> None:
    """Choices are structure, not prose — they must not survive in the body."""
    story = MarkdownStoryParser().parse(tiny_source, slug="tiny")

    assert "[[" not in story.passages["start"].body
    assert "A door, and a window." in story.passages["start"].body


def test_parses_passage_tags_from_the_heading(tiny_source: str) -> None:
    story = MarkdownStoryParser().parse(tiny_source, slug="tiny")

    assert story.passages["window"].tags == ["ending"]
    assert story.passages["start"].tags == []


def test_rejects_a_file_with_no_frontmatter() -> None:
    with pytest.raises(StoryParseError):
        MarkdownStoryParser().parse("## start\n\nNo metadata here.\n", slug="broken")


def test_rejects_a_file_with_no_passages() -> None:
    with pytest.raises(StoryParseError):
        MarkdownStoryParser().parse("---\ntitle: Empty\nstart: nowhere\n---\n", slug="broken")


def test_dangling_targets_survive_parsing(tiny_source: str) -> None:
    """A choice pointing nowhere is a graph problem, not a parse failure.

    Reporting it here would mean an author fixes one broken link per run.
    `graph.validate_story` reports them all at once instead.
    """
    source = tiny_source.replace("[[Open the door->door]]", "[[Open the door->missing]]")
    story = MarkdownStoryParser().parse(source, slug="tiny")

    assert story.passages["start"].choices[0].target == "missing"
