"""Tests for story discovery and the catalogue.

These tests build their stories in `tmp_path` rather than adding fixtures to
`tests/fixtures/stories/`. That is deliberate: the library deliberately *lists*
stories it cannot parse, so a broken fixture added to the shared directory
would surface in the library index `test_web.py` asserts against. Writing the
exact directory each test describes also means a test states its own situation
instead of referring to one three directories away.

What is asserted here is behaviour a caller can observe — a story is listed, a
slug is refused, a second parser is dispatched to — not the private helpers
that produce it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cyoa.engine.markdown_parser import MarkdownStoryParser
from cyoa.engine.models import Passage, Story
from cyoa.engine.parser import StoryParseError
from cyoa.library import StoryLibrary, StoryNotFoundError

VALID = """\
---
title: A Valid Story
author: A. Nonymous
description: One that parses and validates.
start: start
---

## start

The only room.

[[Leave->way-out]]

## way-out [ending]

Outside, at last.
"""

#: No frontmatter at all, so the parser refuses it outright.
UNPARSEABLE = """\
## start

A file with no frontmatter is not a story.
"""

#: Parses cleanly, but `validate_story` reports a dangling target — an ERROR,
#: which is what makes a story unplayable rather than merely suspect.
DANGLING = """\
---
title: A Dangling Story
start: start
---

## start

A door.

[[Open it->nowhere]]
"""

#: Parses and has no errors, only a `dead_end` warning: the start passage
#: stops without being tagged `ending`.
WARNED = """\
---
title: A Warned Story
start: start
---

## start

It simply stops.
"""


def _write_story(root: Path, slug: str, source: str, *, filename: str = "story.md") -> Path:
    """Write one story file into `root/slug/`, creating directories as needed."""
    directory = root / slug
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(source, encoding="utf-8")
    return path


class _TweeishParser:
    """A stand-in second parser, claiming `.twee`.

    Exists to prove the claim `CLAUDE.md` makes about the parser boundary: that
    another story format is a new parser class and nothing else. It records the
    source it was handed, which also shows the loader passes raw file text
    through rather than pre-processing any syntax of its own.
    """

    extensions: tuple[str, ...] = (".twee",)

    def __init__(self, title: str = "From Twee") -> None:
        self.title = title
        self.seen: list[str] = []

    def parse(self, source: str, *, slug: str) -> Story:
        self.seen.append(source)
        return Story(
            slug=slug,
            title=self.title,
            start="start",
            passages={"start": Passage(id="start", body=source.strip(), tags=["ending"])},
        )


@pytest.fixture
def library(tmp_path: Path) -> StoryLibrary:
    """A library over an empty `tmp_path`, to be populated by each test.

    Constructed before any story is written on purpose — the library must read
    the directory when asked, not when built.
    """
    return StoryLibrary(tmp_path, [MarkdownStoryParser()])


# --- the catalogue ----------------------------------------------------------


def test_list_stories_is_empty_when_there_are_no_stories(library: StoryLibrary) -> None:
    assert library.list_stories() == []


def test_list_stories_is_empty_when_the_root_does_not_exist(tmp_path: Path) -> None:
    """A stories volume that failed to mount should be an empty shelf, not a crash."""
    library = StoryLibrary(tmp_path / "never-created", [MarkdownStoryParser()])

    assert library.list_stories() == []


def test_list_stories_finds_a_story_on_disk(library: StoryLibrary, tmp_path: Path) -> None:
    _write_story(tmp_path, "valid", VALID)

    summaries = library.list_stories()

    assert [summary.slug for summary in summaries] == ["valid"]
    assert summaries[0].title == "A Valid Story"


def test_list_stories_carries_the_metadata_the_shelf_shows(
    library: StoryLibrary, tmp_path: Path
) -> None:
    _write_story(tmp_path, "valid", VALID)

    summary = library.list_stories()[0]

    assert summary.author == "A. Nonymous"
    assert summary.description == "One that parses and validates."


def test_list_stories_sorts_by_title_ignoring_case(library: StoryLibrary, tmp_path: Path) -> None:
    """Case-sensitive sorting would file every capitalised title ahead of every
    lowercase one, which is not an order a reader looking at a shelf expects."""
    _write_story(tmp_path, "bandit", VALID.replace("A Valid Story", "Bandit King"))
    _write_story(tmp_path, "apple", VALID.replace("A Valid Story", "apple orchard"))

    titles = [summary.title for summary in library.list_stories()]

    assert titles == ["apple orchard", "Bandit King"]


def test_a_story_added_after_construction_appears_without_a_restart(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """The v1 success metric: drop a file into the directory and it plays."""
    assert library.list_stories() == []

    _write_story(tmp_path, "valid", VALID)

    assert [summary.slug for summary in library.list_stories()] == ["valid"]


def test_a_directory_with_no_story_file_is_not_listed(
    library: StoryLibrary, tmp_path: Path
) -> None:
    (tmp_path / "not-a-story").mkdir()

    assert library.list_stories() == []


def test_a_story_file_no_parser_claims_is_not_listed(library: StoryLibrary, tmp_path: Path) -> None:
    """Only the parsers a library was built with decide what counts as a story."""
    _write_story(tmp_path, "prose", VALID, filename="story.txt")

    assert library.list_stories() == []


def test_a_loose_file_beside_the_stories_is_not_listed(
    library: StoryLibrary, tmp_path: Path
) -> None:
    (tmp_path / "README.md").write_text("Not a story.", encoding="utf-8")

    assert library.list_stories() == []


# --- broken stories are visible, not absent ---------------------------------


def test_a_story_that_cannot_be_parsed_is_still_listed(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """An author with a typo needs to see the story and a problem, not an empty
    shelf that is indistinguishable from a volume that did not mount."""
    _write_story(tmp_path, "broken", UNPARSEABLE)

    assert [summary.slug for summary in library.list_stories()] == ["broken"]


def test_a_story_that_cannot_be_parsed_is_marked_unplayable(
    library: StoryLibrary, tmp_path: Path
) -> None:
    _write_story(tmp_path, "broken", UNPARSEABLE)

    assert library.list_stories()[0].is_playable is False


def test_an_unparseable_story_is_listed_under_its_slug(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """Its title lives in frontmatter that could not be read, so the slug is the
    only name available."""
    _write_story(tmp_path, "broken", UNPARSEABLE)

    assert library.list_stories()[0].title == "broken"


def test_a_story_with_a_validation_error_is_marked_unplayable(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """It parses, so the parser is content; the graph is what rejects it."""
    _write_story(tmp_path, "dangling", DANGLING)

    summary = library.list_stories()[0]

    assert summary.title == "A Dangling Story"
    assert summary.is_playable is False


def test_a_story_with_only_warnings_is_still_playable(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """Warnings are for review, not refusal — an untagged ending still reads."""
    _write_story(tmp_path, "warned", WARNED)

    assert library.list_stories()[0].is_playable is True


def test_one_broken_story_does_not_hide_the_others(library: StoryLibrary, tmp_path: Path) -> None:
    _write_story(tmp_path, "broken", UNPARSEABLE)
    _write_story(tmp_path, "valid", VALID)

    playable = {summary.slug: summary.is_playable for summary in library.list_stories()}

    assert playable == {"broken": False, "valid": True}


# --- loading one story ------------------------------------------------------


def test_load_returns_the_parsed_story(library: StoryLibrary, tmp_path: Path) -> None:
    _write_story(tmp_path, "valid", VALID)

    story = library.load("valid")

    assert story.slug == "valid"
    assert story.start == "start"
    assert set(story.passages) == {"start", "way-out"}


def test_load_raises_for_a_slug_that_is_not_on_disk(library: StoryLibrary) -> None:
    with pytest.raises(StoryNotFoundError):
        library.load("no-such-story")


def test_load_lets_a_parse_error_through(library: StoryLibrary, tmp_path: Path) -> None:
    """`list_stories` degrades a broken story to a stub; `load` must not — a
    caller asking for one story specifically needs to know why it failed."""
    _write_story(tmp_path, "broken", UNPARSEABLE)

    with pytest.raises(StoryParseError):
        library.load("broken")


def test_load_returns_a_story_that_has_validation_errors(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """Validation is the caller's to run. A dangling target is constructible, so
    loading it is not the loader's decision to refuse."""
    _write_story(tmp_path, "dangling", DANGLING)

    assert library.load("dangling").title == "A Dangling Story"


# --- slugs arrive from URLs -------------------------------------------------


@pytest.mark.parametrize("slug", ["../secrets", "../../secrets", "secrets/../../secrets"])
def test_load_refuses_a_slug_that_escapes_the_stories_directory(tmp_path: Path, slug: str) -> None:
    """A real, parseable story is planted outside the root: if the slug were
    joined to the path unchecked, these would resolve to it and load cleanly."""
    root = tmp_path / "stories"
    root.mkdir()
    _write_story(tmp_path, "secrets", VALID)
    library = StoryLibrary(root, [MarkdownStoryParser()])

    with pytest.raises(StoryNotFoundError):
        library.load(slug)


@pytest.mark.parametrize("slug", ["/etc/passwd", ".", "..", "", "Upper", "has space", "a/b"])
def test_load_refuses_a_slug_that_is_not_a_single_safe_segment(
    library: StoryLibrary, slug: str
) -> None:
    with pytest.raises(StoryNotFoundError):
        library.load(slug)


def test_a_story_directory_that_is_not_url_safe_is_not_listed(
    library: StoryLibrary, tmp_path: Path
) -> None:
    """The same rule applies in both directions: a directory the loader would
    refuse to load must not be advertised in the catalogue either."""
    _write_story(tmp_path, "Not Url Safe", VALID)

    assert library.list_stories() == []


# --- the parser boundary ----------------------------------------------------


def test_a_second_parser_claims_its_own_extension(tmp_path: Path) -> None:
    """Evidence for the Twee claim in `CLAUDE.md`: a new format is a new parser
    class handed to the library, with no change to the loader."""
    twee = _TweeishParser()
    library = StoryLibrary(tmp_path, [MarkdownStoryParser(), twee])
    _write_story(tmp_path, "ported", "Not markdown at all.", filename="story.twee")

    story = library.load("ported")

    assert story.title == "From Twee"


def test_a_parser_is_handed_the_raw_file_text(tmp_path: Path) -> None:
    """Nothing outside the parser layer touches story-file syntax, so what the
    parser receives is exactly what is on disk."""
    twee = _TweeishParser()
    library = StoryLibrary(tmp_path, [twee])
    _write_story(tmp_path, "ported", ":: start\nRaw twee syntax.\n", filename="story.twee")

    library.load("ported")

    assert twee.seen == [":: start\nRaw twee syntax.\n"]


def test_both_formats_can_sit_in_one_library(tmp_path: Path) -> None:
    library = StoryLibrary(tmp_path, [MarkdownStoryParser(), _TweeishParser()])
    _write_story(tmp_path, "markdown-one", VALID)
    _write_story(tmp_path, "twee-one", "Not markdown.", filename="story.twee")

    titles = {summary.slug: summary.title for summary in library.list_stories()}

    assert titles == {"markdown-one": "A Valid Story", "twee-one": "From Twee"}


def test_parser_order_decides_when_a_story_has_both_formats(tmp_path: Path) -> None:
    """Which file wins is the library's dispatch order, not the filesystem's."""
    library = StoryLibrary(tmp_path, [_TweeishParser(), MarkdownStoryParser()])
    _write_story(tmp_path, "ambiguous", VALID)
    _write_story(tmp_path, "ambiguous", "Not markdown.", filename="story.twee")

    assert library.load("ambiguous").title == "From Twee"
