"""Story graph validation.

A story is a directed graph of passages. The mistakes authors actually make
are graph mistakes — a choice pointing at a passage that was renamed, a
section orphaned by a typo, a branch that stops mid-sentence. Catching those
before a reader hits them is most of what makes this engine worth having,
so validation reports *every* issue in one pass rather than raising on the
first.

Nothing here touches file syntax; it operates purely on a parsed `Story`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from cyoa.engine.models import Story


class Severity(StrEnum):
    """How much an issue matters.

    ERROR means the story can strand a reader and should not be playable.
    WARNING means it is probably a mistake but the story still works.
    """

    ERROR = "error"
    WARNING = "warning"


class ValidationIssue(BaseModel):
    """One problem found in a story graph."""

    severity: Severity
    code: str
    message: str
    passage_id: str | None = None


def validate_story(story: Story) -> list[ValidationIssue]:
    """Check `story` for graph problems and return everything found.

    Checks:
        - `dangling_target` (ERROR): a choice points at a passage id that does
          not exist in the story.
        - `missing_start` (ERROR): `start` names a passage that does not exist.
        - `unreachable_passage` (WARNING): a passage no path from `start` can
          reach. Usually a rename that missed a reference.
        - `dead_end` (WARNING): a terminal passage not tagged `ending`.
          Endings are inferred rather than declared, so the parser cannot tell
          a finished branch from an abandoned one. Tagging a passage `ending`
          is how an author says "this stop is on purpose"; anything else that
          stops gets flagged for review.

    Returns:
        Every issue found, in no guaranteed order. An empty list means the
        story is playable.
    """
    raise NotImplementedError


def reachable_from(story: Story, start: str | None = None) -> set[str]:
    """Return the ids of every passage reachable from `start`.

    Defaults to the story's declared start passage. Used by validation, and by
    anything that needs to know the true extent of a story — a completion
    percentage, or an editor's map view later on.
    """
    raise NotImplementedError
