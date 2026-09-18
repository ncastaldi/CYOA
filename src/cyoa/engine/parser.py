"""The parser boundary.

Every story format CYOA supports is a `StoryParser` implementation. Nothing
outside this package may inspect raw story-file syntax — no route, template,
or repository gets to run its own `[[...]]` regex. That single rule is what
keeps the on-disk format a decision we can revisit (see the Twee question in
`CLAUDE.md`) instead of one baked into the whole application.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cyoa.engine.models import Story


class StoryParseError(Exception):
    """Raised when a source file cannot be turned into a `Story` at all.

    Reserved for structural failures — unreadable frontmatter, a missing
    required field, no passages at all, duplicate passage ids. Problems that
    still yield a constructible story (a dangling choice target, an
    unreachable passage, a `start` naming a passage that does not exist) are
    *not* errors here; they are reported by `graph.validate_story` so an
    author sees every issue at once rather than one per run.
    """


@runtime_checkable
class StoryParser(Protocol):
    """Translates one source format into the internal `Story` model."""

    #: File suffixes this parser claims, e.g. `(".md",)`. Used by the library
    #: loader to pick a parser for a discovered file.
    extensions: tuple[str, ...]

    def parse(self, source: str, *, slug: str) -> Story:
        """Parse `source` into a `Story` identified by `slug`.

        Raises:
            StoryParseError: if `source` is not a usable story.
        """
        ...
