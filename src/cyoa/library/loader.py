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

from pathlib import Path

from pydantic import BaseModel

from cyoa.engine.models import Story
from cyoa.engine.parser import StoryParser


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
        raise NotImplementedError

    def load(self, slug: str) -> Story:
        """Parse and return one story in full.

        Raises:
            StoryNotFoundError: if no story with that slug is on disk.
            StoryParseError: if the file exists but cannot be parsed.
        """
        raise NotImplementedError


class StoryNotFoundError(Exception):
    """Raised when a requested story slug is not present in the library."""
