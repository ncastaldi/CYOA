"""Discovers stories on disk and builds the playable catalogue.

The library is the bridge between a directory of files and the engine's world
of `Story` objects: it walks the stories directory, picks a parser per file
suffix, and hands the source text over. It does not itself understand any
story format — see the parser-boundary rule in `../engine/README.md`.

The success metric for v1 runs straight through this module: a file someone
drops into `stories/` should appear in the library and play, with no code
change and no restart. That rules out loading the catalogue once at startup.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel

from cyoa.engine.graph import Severity, validate_story
from cyoa.engine.models import Story
from cyoa.engine.parser import StoryParseError, StoryParser

#: A slug is a single path segment, lowercase, hyphen or underscore separated.
#: Slugs arrive from the URL, so this is also what keeps `load("../../etc")`
#: from resolving outside the stories directory.
_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

#: Every story is a single `story.<ext>` file in its own directory. The
#: extension picks the parser, which is what makes adding Twee a new parser
#: class rather than a change here.
_STEM = "story"


class StorySummary(BaseModel):
    """What the library index needs to show a story without parsing all of it."""

    slug: str
    title: str
    author: str | None = None
    description: str | None = None
    is_playable: bool = True


class StoryLibrary:
    """A directory of stories, re-read as it changes.

    Args:
        root: The stories directory. Each story is `<root>/<slug>/story.md`.
        parsers: Parsers to dispatch across, by file suffix.
    """

    def __init__(self, root: Path, parsers: list[StoryParser]) -> None:
        self.root = root
        self.parsers = parsers

    def list_stories(self) -> list[StorySummary]:
        """Return a summary of every story in the library, sorted by title.

        A story whose file fails to parse is still listed, with
        `is_playable=False` — a broken story should be visibly broken rather
        than silently absent, or an author has no way to tell a typo from a
        mount that did not come up.
        """
        summaries = [self._summarise(slug) for slug in self._story_slugs()]
        return sorted(summaries, key=lambda summary: summary.title.casefold())

    def load(self, slug: str) -> Story:
        """Parse and return one story in full.

        Raises:
            StoryNotFoundError: if no story with that slug is on disk.
            StoryParseError: if the file exists but cannot be parsed.
        """
        found = self._story_file(slug)
        if found is None:
            raise StoryNotFoundError(f"no story with slug {slug!r} in {self.root}")

        path, parser = found
        return parser.parse(path.read_text(encoding="utf-8"), slug=slug)

    def _summarise(self, slug: str) -> StorySummary:
        """Build one catalogue entry, degrading to an unplayable stub on failure.

        A story that cannot be parsed, cannot be read, or that `validate_story`
        rejects outright is listed under its slug and marked unplayable. The
        alternative — dropping it — leaves an author staring at a shelf with no
        clue whether they made a typo or mounted the wrong volume.
        """
        try:
            story = self.load(slug)
        except (StoryParseError, StoryNotFoundError, OSError, UnicodeDecodeError):
            return StorySummary(slug=slug, title=slug, is_playable=False)

        blocking = any(issue.severity is Severity.ERROR for issue in validate_story(story))
        return StorySummary(
            slug=story.slug,
            title=story.title,
            author=story.author,
            description=story.description,
            is_playable=not blocking,
        )

    def _story_slugs(self) -> Iterator[str]:
        """Yield the slug of every story directory holding a parseable file.

        Re-read on every call rather than cached at startup: dropping a file
        into the stories directory should make it appear without a restart.
        """
        if not self.root.is_dir():
            return

        for entry in sorted(self.root.iterdir()):
            if entry.is_dir() and self._story_file(entry.name) is not None:
                yield entry.name

    def _story_file(self, slug: str) -> tuple[Path, StoryParser] | None:
        """Resolve a slug to its story file and the parser that claims it.

        Returns None when the slug is not a single safe path segment, so a
        crafted `slug` from a URL cannot walk out of the stories directory.
        """
        if not _SLUG.match(slug):
            return None

        directory = self.root / slug
        if not directory.is_dir():
            return None

        for parser in self.parsers:
            for extension in parser.extensions:
                candidate = directory / f"{_STEM}{extension}"
                if candidate.is_file():
                    return candidate, parser
        return None


class StoryNotFoundError(Exception):
    """Raised when a requested story slug is not present in the library."""
