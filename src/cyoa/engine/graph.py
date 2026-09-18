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
    issues: list[ValidationIssue] = []

    if story.start not in story.passages:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="missing_start",
                message=f"start passage {story.start!r} does not exist",
            )
        )

    for passage_id, passage in story.passages.items():
        for choice in passage.choices:
            if choice.target not in story.passages:
                issues.append(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="dangling_target",
                        message=(
                            f"choice {choice.text!r} points at {choice.target!r}, "
                            f"which is not a passage in this story"
                        ),
                        passage_id=passage_id,
                    )
                )

    # Reachability is computed even when errors exist. A dangling link makes
    # the warnings below noisier, but suppressing them would mean an author
    # fixes errors, re-runs, and only then learns what else is wrong — which is
    # the one-problem-per-run loop this whole function exists to avoid.
    reachable = reachable_from(story)

    for passage_id, passage in story.passages.items():
        if passage_id not in reachable:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="unreachable_passage",
                    message=f"no path from {story.start!r} reaches this passage",
                    passage_id=passage_id,
                )
            )
        if passage.is_ending and "ending" not in passage.tags:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="dead_end",
                    message=(
                        "passage offers no choices; tag it 'ending' if stopping here is intentional"
                    ),
                    passage_id=passage_id,
                )
            )

    return issues


def reachable_from(story: Story, start: str | None = None) -> set[str]:
    """Return the ids of every passage reachable from `start`.

    Defaults to the story's declared start passage. Used by validation, and by
    anything that needs to know the true extent of a story — a completion
    percentage, or an editor's map view later on.

    A `start` that does not exist yields an empty set rather than raising:
    validation reports that as `missing_start`, and this should not be the
    thing that fails first.
    """
    origin = story.start if start is None else start
    if origin not in story.passages:
        return set()

    seen = {origin}
    pending = [origin]
    while pending:
        passage = story.passages[pending.pop()]
        for choice in passage.choices:
            # Dangling targets are reported separately; they simply lead nowhere.
            if choice.target in story.passages and choice.target not in seen:
                seen.add(choice.target)
                pending.append(choice.target)

    return seen
