# Writing a story for CYOA

This is for you if someone handed you this repo and asked you to write a
choose-your-own-adventure story — not to build anything, just to write. You
don't need to know Python, or run any code, to do this. You need a text
editor and this document.

If you want, skip straight to the [template](#template) at the bottom, copy
it, and start replacing the placeholder text. Come back here when something's
unclear.

## What you're making

One file: `story.md`. It's plain text — no software required to write it,
though a plain text editor (Notepad, TextEdit, VS Code) works better than a
word processor, which will fight you over smart quotes and auto-formatting.

A story is a set of **passages** — pages, basically — connected by
**choices**. The reader starts at one passage, picks a choice, lands on the
next passage, picks again, and so on until they reach a passage with no
choices left. That's an ending. Most stories have several.

## The shape of the file

```markdown
---
title: The Cave
author: Your Name
description: One line for the library index.
start: mouth
---

## mouth

Cold air pushes out of the opening in the rock.

[[Go in->tunnel]]
[[Turn back->trail]]

## tunnel

The passage narrows, then opens into a room you can't see the edges of.

[[Light a match->room]]
[[Feel your way forward->room]]

## trail [ending]

You walk back down while there's still light to see by.

## room [ending]

Whatever's in here, you're not alone with it anymore.
```

Three moving parts:

### 1. The top block (frontmatter)

The bit between the two `---` lines at the very top. It's metadata, not
story text — the reader never sees `title:` or `start:` written out, but the
engine needs them to know your story's name and where it begins.

- `title` — required. The name readers see.
- `start` — required. The id of the passage the story opens on (see below).
- `author` — optional. Your name, or a pen name.
- `description` — optional. One sentence, shown in the story list.

### 2. Passages

Each passage starts with `##` followed by its **id** — a short label,
lowercase, no spaces (use hyphens or underscores instead: `dark-room`, not
`Dark Room`). The id is how choices refer to this passage, so it needs to be
unique within the story, but the reader never sees it.

Everything after the `##` line, up to the next `##` line, is that passage's
text. Write it like you'd write any prose — paragraphs, dialogue,
whatever the scene needs. Blank lines between paragraphs are preserved.
Basic Markdown works if you want *italics*, **bold**, or lists, but you
don't need any of that — plain sentences are completely fine.

### 3. Choices

A line that looks exactly like this:

```markdown
[[Go in->tunnel]]
```

`Go in` is what the reader sees on the button. `tunnel` is the id of the
passage it leads to. Put one of these on its own line for every option you
want to offer at that passage. The order you write them in is the order
they appear on the page.

**A passage with no choice lines is an ending.** You don't declare an
ending specially — you just stop offering ways out. It's good practice to
mark it so anyone checking your story knows the stop was on purpose (see
[Endings](#endings) below).

## Endings

Tag an ending passage like this:

```markdown
## trail [ending]
```

That `[ending]` after the id tells anyone validating the story "yes, this is
supposed to stop here." If you leave it off, the story still works exactly
the same for a reader — but a checking tool will flag that passage as a
possible mistake, because a passage with no choices and no `[ending]` tag
looks identical to a branch you forgot to finish. When in doubt, tag it.

## Rules that will bite you if you don't know them

- **Ids are lowercase, no spaces.** `dark-room` or `dark_room`, never
  `Dark Room` or `dark room`.
- **Every id must be unique.** Two passages named `## room` will break the
  whole story.
- **A choice can point to a passage defined anywhere in the file** — before
  or after it. Order in the file doesn't matter for choices, only for how
  passages read if someone opens the raw file.
- **A choice's target has to exist.** If you write
  `[[Open the door->door]]` and there's no `## door` passage anywhere in
  the file, that choice leads nowhere and the story won't be considered
  finished. (The [checker](#checking-your-work-yourself) below catches
  this for you — you don't have to proofread every link by eye.)
- **A choice line has to be its own line, with nothing else on it.** If you
  want to write a sentence that happens to mention double brackets, that's
  fine — a line only counts as a choice if, after trimming spaces, the
  *entire* line is `[[text->target]]`.
- **Every passage should be reachable from the start.** If nothing links to
  a passage you wrote, a reader will never see it. This is the second most
  common mistake (after typos in ids) and it's an easy one to make when a
  passage gets renamed partway through writing.

## Checking your work yourself

You don't have to wait for whoever gave you this repo to tell you your
story has a broken link. If you (or they) have the project set up, there's
a one-line check:

```
python scripts/validate_story.py path/to/your/story.md
```

It reads your file the same way the real app does and tells you, in plain
language, whether it parses at all and whether every choice actually leads
somewhere. Run it after every editing session — it takes a second and it's
much less frustrating than being told "passage 3 doesn't exist" after
you've already moved on to writing passage 12.

A clean run looks like this:

```
"The Cave" — 3 passages

No problems found. This story is ready to read.
```

A broken one tells you exactly what to fix:

```
"The Cave" — 3 passages

1 problem to fix:
  - choice 'Go in' points at 'tunel', which is not a passage in this story (passage: mouth)
```

(That one's a typo — `tunel` instead of `tunnel`.)

## Delivering your story

Send back the `story.md` file (and let them know what you'd like the folder
/ URL slug to be — lowercase, hyphens instead of spaces, e.g. `the-cave`).
That's the whole handoff. Nothing else needs to change for your story to
show up and be playable.

## What this format can't do yet

Worth knowing up front so you don't design around a feature that isn't
there: no conditions (a choice that only appears if the reader did
something earlier), no inventory or stats, no images. It's branching prose
and nothing else, for now. If your story idea depends on one of those,
mention it — it might be worth doing anyway with the constraint in mind, or
it might be a good reason to wait.

## Template

Copy everything below into a new `story.md` and start replacing text.
Delete the example passages, or keep the shape and rewrite them in place —
whichever's easier to think in.

```markdown
---
title: 
author: 
description: 
start: start
---

## start

Where your story begins. Set the scene, then offer the first choice.

[[First option->first-branch]]
[[Second option->second-branch]]

## first-branch

What happens if the reader picks the first option.

[[Continue->ending-one]]

## second-branch

What happens if the reader picks the second option.

[[Continue->ending-two]]

## ending-one [ending]

One way this story can end.

## ending-two [ending]

Another way this story can end.
```
