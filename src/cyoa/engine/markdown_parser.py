"""Markdown + YAML frontmatter story parser — the v1 format.

A story is one file. YAML frontmatter carries story metadata; `##` headings
open passages; `[[Choice text->target_id]]` lines are the ways out. The
normative description lives in `docs/specs/spec-story-format.md`; this module
is the only code permitted to know any of it.

    ---
    title: The Cave
    start: mouth
    ---

    ## mouth

    Cold air pushes out of the opening.

    [[Go in->tunnel]]
    [[Turn back->home]]
"""

from __future__ import annotations

import re

import yaml

from cyoa.engine.models import Choice, Passage, Story
from cyoa.engine.parser import StoryParseError

#: Frontmatter opens and closes on a line that is exactly this.
_DELIMITER = "---"

#: `## passage_id` with an optional `[tag, tag]` suffix. The id may not contain
#: whitespace, which is what lets the optional bracket group be unambiguous.
_HEADING = re.compile(r"^##\s+(?P<id>\S+?)\s*(?:\[(?P<tags>[^\]]*)\])?\s*$")

#: A choice is a whole line and nothing else. `.+?` is lazy so the split falls
#: on the *first* `->`, letting choice text contain arrows.
_CHOICE = re.compile(r"^\[\[(?P<text>.+?)->(?P<target>[^\]]+)\]\]$")

#: Some editors prefix a file with a byte-order mark, which would otherwise
#: make the first line fail the delimiter check. Written as chr() rather than
#: a literal, which would be an invisible character sitting in the source.
_BOM = chr(0xFEFF)


class MarkdownStoryParser:
    """Parses the Markdown + frontmatter format into a `Story`.

    Implements the `StoryParser` protocol.
    """

    extensions: tuple[str, ...] = (".md",)

    def parse(self, source: str, *, slug: str) -> Story:
        """Parse Markdown source into a `Story`.

        Raises:
            StoryParseError: if frontmatter is missing or unreadable, if a
                required frontmatter field is absent, if the file declares no
                passages, or if two passages share an id.

        A `start` that names a passage which does not exist is *not* a parse
        error — the story is still constructible, so `graph.validate_story`
        reports it as `missing_start` alongside every other graph problem.
        """
        metadata, body_lines = _split_frontmatter(source.removeprefix(_BOM))

        title = metadata.get("title")
        start = metadata.get("start")
        if not isinstance(title, str) or not title:
            raise StoryParseError(f"story {slug!r} is missing a 'title' in its frontmatter")
        if not isinstance(start, str) or not start:
            raise StoryParseError(f"story {slug!r} is missing a 'start' in its frontmatter")

        passages = _parse_passages(body_lines, slug=slug)
        if not passages:
            raise StoryParseError(f"story {slug!r} declares no passages")

        author = metadata.get("author")
        description = metadata.get("description")
        return Story(
            slug=slug,
            title=title,
            start=start,
            passages=passages,
            author=author if isinstance(author, str) else None,
            description=description if isinstance(description, str) else None,
        )


def _split_frontmatter(source: str) -> tuple[dict[str, object], list[str]]:
    """Split source into its parsed frontmatter mapping and the remaining lines."""
    lines = source.splitlines()
    if not lines or lines[0].strip() != _DELIMITER:
        raise StoryParseError("file does not open with a '---' frontmatter block")

    for index in range(1, len(lines)):
        if lines[index].strip() == _DELIMITER:
            raw = "\n".join(lines[1:index])
            break
    else:
        raise StoryParseError("frontmatter block is never closed with '---'")

    try:
        metadata = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise StoryParseError(f"frontmatter is not valid YAML: {exc}") from exc

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise StoryParseError("frontmatter must be a mapping of fields to values")

    return metadata, lines[index + 1 :]


def _parse_passages(lines: list[str], *, slug: str) -> dict[str, Passage]:
    """Build every passage found in `lines`, in document order."""
    passages: dict[str, Passage] = {}
    current_id: str | None = None
    current_tags: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if current_id is None:
            return
        if current_id in passages:
            raise StoryParseError(f"story {slug!r} defines passage {current_id!r} more than once")
        body, choices = _split_choices(buffer)
        passages[current_id] = Passage(id=current_id, body=body, choices=choices, tags=current_tags)

    for line in lines:
        heading = _HEADING.match(line)
        if heading is None:
            buffer.append(line)
            continue

        flush()
        current_id = heading.group("id")
        current_tags = _parse_tags(heading.group("tags"))
        buffer = []

    flush()
    return passages


def _parse_tags(raw: str | None) -> list[str]:
    """Turn a `[a, b]` heading suffix into a list, dropping empty entries."""
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _split_choices(lines: list[str]) -> tuple[str, list[Choice]]:
    """Separate a passage's prose from its choice lines.

    A line counts as a choice only when that is its entire content. A `[[...]]`
    sitting alongside other text is prose — the rule stays simple to state, and
    an author who wants to write about double brackets can.
    """
    body_lines: list[str] = []
    choices: list[Choice] = []

    for line in lines:
        match = _CHOICE.match(line.strip())
        if match is None:
            body_lines.append(line)
            continue
        choices.append(
            Choice(text=match.group("text").strip(), target=match.group("target").strip())
        )

    # Trim blank lines at either end — including those left behind by removed
    # choices — while preserving interior blank lines and any indentation,
    # which Markdown treats as meaningful.
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    return "\n".join(body_lines), choices
