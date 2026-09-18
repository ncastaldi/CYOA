"""The internal story model.

This module defines what a story *is* to CYOA, independent of how it was
written on disk. Parsers in this package translate a source format (Markdown
with frontmatter today, possibly Twee later) into these types; everything
downstream — validation, play state, the web layer — reads only these.

Keeping the model format-agnostic is what makes the story format swappable.
See `../../../docs/specs/spec-story-format.md` for the on-disk format.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Choice(BaseModel):
    """A single branch out of a passage.

    `target` is the id of the passage this choice leads to. It is not resolved
    to a `Passage` object at parse time — a story may legitimately reference a
    passage defined later in the file, and dangling targets are reported by
    `graph.validate_story` rather than raised during parsing.
    """

    text: str = Field(min_length=1)
    target: str = Field(min_length=1)


class Passage(BaseModel):
    """One addressable node of a story: some prose, and the ways out of it."""

    id: str = Field(min_length=1)
    body: str = ""
    choices: list[Choice] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @property
    def is_ending(self) -> bool:
        """True when this passage has no way out — i.e. it ends the story.

        Endings are inferred, not declared. An author writes a passage with no
        choices; they do not mark it. That keeps a dead end (a mistake) and an
        ending (intentional) textually identical, which is why `graph` reports
        unreachable-and-untagged terminals for review rather than silently
        accepting them.
        """
        return not self.choices


class Story(BaseModel):
    """A complete, parsed story: metadata plus its passage graph."""

    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    start: str = Field(min_length=1)
    passages: dict[str, Passage] = Field(default_factory=dict)
    author: str | None = None
    description: str | None = None

    def passage(self, passage_id: str) -> Passage | None:
        """Look up a passage by id, or None if the story has no such passage."""
        return self.passages.get(passage_id)
