# Stories

Story content. One folder per story, each containing a `story.md`:

```
stories/
├── example/
│   └── story.md
└── your-story/
    └── story.md
```

The folder name is the story's slug — it appears in URLs, so keep it lowercase with hyphens.

In production this directory is mounted into the container as a volume, so adding a story is a file copy. It is re-read as it changes: a story you drop in shows up in the library without a restart.

## Writing one

A story is Markdown with YAML frontmatter. Frontmatter carries the story's metadata; `##` headings open passages; `[[Choice text->target_id]]` lines are the ways out.

```markdown
---
title: The Cave
author: Your Name
description: One line for the library index.
start: mouth
---

## mouth

Cold air pushes out of the opening.

[[Go in->tunnel]]
[[Turn back->trail]]

## trail [ending]

You walk back down while there is still light.
```

A passage with no choices is an ending — you do not declare it, you just stop offering choices. Tagging it `[ending]` is how you tell the engine the stop was on purpose; an untagged passage that stops gets flagged as a possible dead end when the story is validated.

**The full format, including every field and error case, is specified in [`../docs/specs/spec-story-format.md`](../docs/specs/spec-story-format.md).** That document is normative; this README is the quick version.

## What belongs here

- Story folders, each with a `story.md`
- Any per-story assets a future version supports (none yet — v1 is text only)

## What does not belong here

- Test fixtures (those go in `tests/fixtures/stories/`)
- Application code of any kind

## Conventions

- Folder names and passage ids are lowercase with hyphens or underscores, so they are safe in URLs without escaping.
- Every story needs `title` and `start` in its frontmatter. Everything else is optional.
- Prose is prose. Write in Markdown; the engine renders it. You should never need to think about HTML.
