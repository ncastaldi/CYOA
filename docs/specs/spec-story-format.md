# Spec — Story Format (Markdown + YAML frontmatter)

**Status**: Draft v0.1
**Date**: 2026-09-18
**Implements**: `src/cyoa/engine/markdown_parser.py`
**Tested by**: `tests/test_parser.py`

This document is normative. `stories/README.md` is the friendly summary; where the two disagree, this one is correct.

---

## Design intent

Authors are people and LLMs, not programmers. The format's job is to let someone write a *story* rather than a data structure, while still being unambiguous enough to parse without guessing.

Two consequences shape everything below:

- **Prose is the default.** Anything that isn't recognised as structure is prose. An author should never have to escape, quote, or wrap anything to write a normal sentence.
- **Structure is line-oriented and shallow.** Passages open on a heading; choices are whole lines. Nothing nests. This is what makes the format robust to LLM output, which is reliable about lines and unreliable about indentation.

## File location

```
stories/<slug>/story.md
```

`<slug>` is the story's identifier and appears in URLs. Lowercase ASCII letters, digits, hyphens, and underscores. The parser does not read the folder name — the loader passes it in as `slug`.

Files are UTF-8. A leading UTF-8 BOM, if present, is stripped before parsing.

## Overall structure

```
<frontmatter block>
<passage>
<passage>
...
```

## Frontmatter

The file **must** open with a YAML block delimited by `---` on its own line, before any other content:

```markdown
---
title: The Cave
author: Your Name
description: One line for the library index.
start: mouth
---
```

| Field | Required | Type | Meaning |
|---|---|---|---|
| `title` | yes | string | Display name, shown in the library and page title |
| `start` | yes | string | Id of the passage a reader begins at |
| `author` | no | string | Shown in the library |
| `description` | no | string | One-line blurb for the library index |

Unknown fields are ignored rather than rejected — an author adding `mood: bleak` for their own benefit should not break their story. Forward compatibility is worth more here than strictness.

## Passages

A passage opens with a level-2 ATX heading:

```markdown
## mouth
```

The heading text is the passage **id**: lowercase letters, digits, hyphens, and underscores, so it is URL-safe without escaping. Ids must be unique within a story.

A passage extends from its heading to the next `## ` heading or end of file.

### Passage tags

An optional bracketed, comma-separated list may follow the id:

```markdown
## window [ending, good]
```

Whitespace around each tag is stripped. A passage without a bracket has an empty tag list.

Tags are descriptive, with one exception: **`ending` suppresses the `dead_end` warning.** Tagging a passage `ending` is how an author says "stopping here is on purpose"; an untagged terminal passage gets flagged for review. It does not otherwise change behaviour — it is not what *makes* a passage an ending, and tagging a passage with choices `ending` changes nothing.

Every other tag is free-form annotation, there so authors can label their own work and so a future feature (an endings list, a map view) has something to build on.

## Choices

A choice is a line whose entire content, after stripping surrounding whitespace, is:

```markdown
[[Choice text->target_id]]
```

- **Choice text** is what the reader sees on the button. Everything before the first `->` is the text; it may contain any character except `]]`. Leading and trailing whitespace is stripped.
- **target_id** is the id of the passage this choice leads to. Whitespace is stripped.
- Choices are collected in document order, and that is the order they are rendered in.
- A choice target is **not** resolved at parse time. A story may reference a passage defined later in the file, and a target that does not exist anywhere is a graph problem, not a parse failure.

Choice lines are removed from the passage body. `[[` must not survive into rendered prose.

A line containing a `[[...]]` alongside other text is **prose**, not a choice. This keeps the rule simple to state and simple to implement, and means an author who wants to write about double brackets can.

## Body

Everything in a passage that is not its heading and not a choice line is the body. It is Markdown, rendered by the engine.

Leading and trailing blank lines are stripped. Interior blank lines are preserved — paragraph breaks are the author's, not the parser's.

## Endings

**A passage with no choices is an ending.** Authors do not declare endings; they stop offering choices.

This makes an intentional ending and an accidental dead end textually identical, which is deliberate: the parser cannot tell them apart, so `graph.validate_story` surfaces terminal passages for review rather than silently accepting or rejecting them. The author decides.

## Errors

The parser raises `StoryParseError` when a file cannot become a `Story` at all:

| Condition | Why it is fatal |
|---|---|
| No frontmatter block | Nothing identifies the story |
| Frontmatter is not valid YAML | Nothing identifies the story |
| `title` or `start` missing | A required field has no sensible default |
| No passages | There is nothing to read |
| Duplicate passage id | Ambiguous — two passages answer to one link |

Everything else is reported by `graph.validate_story`, which returns **all** issues in one pass rather than raising on the first:

| Code | Severity | Condition |
|---|---|---|
| `dangling_target` | error | A choice points at an id no passage has |
| `missing_start` | error | `start` names a passage that does not exist |
| `unreachable_passage` | warning | No path from `start` reaches this passage |
| `dead_end` | warning | A terminal passage not tagged `ending` |

The split is deliberate. An author fixing a story should see every problem at once; one broken link per run is a miserable way to work.

## Worked example

```markdown
---
title: Tiny
author: Test Suite
description: The smallest story that still branches, ends, and loops.
start: start
---

## start

A door, and a window.

[[Open the door->door]]
[[Climb out the window->window]]

## door

It was locked all along.

[[Try the window instead->window]]

## window [ending]

You climb out into the afternoon.
```

Parses to three passages. `start` has two choices, `door` has one, `window` has none and is therefore an ending. Both `start` and `door` lead to `window`; a passage having several ways in is normal and needs no special handling.

## Deliberately out of scope

- **Conditions and variables** (`if has_lantern`). When these arrive they get a restricted expression evaluator, never `eval` — see constraint 1 in `CLAUDE.md`. The syntax is undesigned.
- **Includes across files.** One story is one file.
- **Inline formatting beyond Markdown.** No custom macros.
- **Non-text assets.** v1 is text only.

## Open question

Twee, the established interactive-fiction format, is structurally close to this one — `:: PassageName` headings and `[[link]]` choices — and the Twine visual editor authors it for free. Whether to adopt it, or support both, is unresolved; see `CLAUDE.md` -> Open questions. The `StoryParser` protocol exists so that answering "both" costs one class.
