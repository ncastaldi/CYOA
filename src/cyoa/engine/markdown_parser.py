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

Not yet implemented — see `CLAUDE.md` -> Current state -> Not started.
"""

from __future__ import annotations

from cyoa.engine.models import Story


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
        raise NotImplementedError
