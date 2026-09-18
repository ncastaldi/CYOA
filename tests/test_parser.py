"""Tests for the Markdown + frontmatter parser.

Written before the implementation; see `docs/specs/spec-story-format.md` for
the normative format these assert against.
"""

from __future__ import annotations

import pytest

from cyoa.engine.markdown_parser import MarkdownStoryParser
from cyoa.engine.parser import StoryParseError


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


def test_tolerates_a_byte_order_mark(tiny_source: str) -> None:
    """Some editors prefix a file with one; it must not break delimiter detection."""
    story = MarkdownStoryParser().parse(chr(0xFEFF) + tiny_source, slug="tiny")

    assert story.title == "Tiny"
    assert set(story.passages) == {"start", "door", "window"}


def test_rejects_a_file_with_no_frontmatter() -> None:
    with pytest.raises(StoryParseError):
        MarkdownStoryParser().parse("## start\n\nNo metadata here.\n", slug="broken")


def test_rejects_unclosed_frontmatter() -> None:
    with pytest.raises(StoryParseError):
        MarkdownStoryParser().parse("---\ntitle: Unfinished\n\n## start\n\nHello.\n", slug="broken")


def test_rejects_duplicate_passage_ids() -> None:
    source = "---\ntitle: Twice\nstart: a\n---\n\n## a\n\nFirst.\n\n## a\n\nSecond.\n"
    with pytest.raises(StoryParseError):
        MarkdownStoryParser().parse(source, slug="broken")


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
